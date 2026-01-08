from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import pandas as pd
import numpy as np
import datetime
import os
import io
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 用于flash消息
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大50MB

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('temp', exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def merge_requirements(r_and_s_path):
    """
    执行合并需求
    
    参数:
    r_and_s_path: 需求及库存更新.xlsx 文件路径
    
    返回:
    (success, message, merged_file_path)
    """
    try:
        # 读取数据（合并需求只需要客户需求表）
        require = pd.read_excel(r_and_s_path, sheet_name='客户需求')
        
        file_length = len(require)
        
        b_ind = require['锦宬半成品料号']
        c_ind = require['锦宬成品料号']
        total = require['合计'].astype('int32')
        
        column_names_3 = ['锦宬成品料号', '合计']
        for item in require:
            if isinstance(item, datetime.datetime):
                column_names_3.append(item)
        
        # 合并需求
        total_c_dict = {}
        total_c_rows = []
        for i in range(0, file_length):
            if total[i] != 0:
                if c_ind[i] not in total_c_dict:
                    total_c_dict[c_ind[i]] = {}
                for item in require:
                    if isinstance(item, datetime.datetime):
                        entry = require[item][i]
                        if item in total_c_dict[c_ind[i]]:
                            total_c_dict[c_ind[i]][item] += entry
                        else:
                            total_c_dict[c_ind[i]][item] = entry
        
        for key in total_c_dict:
            entry = [key]
            total = 0
            for key_time in total_c_dict[key]:
                total += total_c_dict[key][key_time]
            entry.append(total)
            for key_time in total_c_dict[key]:
                entry.append(total_c_dict[key][key_time])
            
            total_c_rows.append(entry)
        
        df_total = pd.DataFrame(total_c_rows, columns=column_names_3)
        
        # 生成合并需求文件名
        merged_file_path = os.path.join('temp', '合并需求' + datetime.datetime.now().strftime('%m-%d') + '_' + str(uuid.uuid4())[:8] + '.xlsx')
        
        with pd.ExcelWriter(merged_file_path) as writer:
            df_total.to_excel(writer, '客户需求', index=False)
        
        return True, "合并需求完成！", merged_file_path
        
    except Exception as e:
        return False, f"合并需求失败：{str(e)}", None


def calculate_schedule(r_and_s_path, c_to_b_workbook_path, merged_file_path):
    """
    执行排程计算
    
    参数:
    r_and_s_path: 需求及库存更新.xlsx 文件路径
    c_to_b_workbook_path: BOM及物料更新.xlsx 文件路径
    merged_file_path: 合并需求文件路径
    
    返回:
    (success, message, output_path)
    """
    try:
        # 读取数据
        require = pd.read_excel(merged_file_path, sheet_name='客户需求')
        storage_c = pd.read_excel(r_and_s_path, sheet_name='成品')
        storage_extra = pd.read_excel(r_and_s_path, sheet_name='超需求库存')
        storage_b = pd.read_excel(r_and_s_path, sheet_name='半品')
        c_to_b_sheet = pd.read_excel(c_to_b_workbook_path, sheet_name='成品与半成品对照表')
        
        # 构建成品与半成品对照字典
        file_length = len(c_to_b_sheet)
        ctb_c = c_to_b_sheet['锦宬成品编码']
        ctb_b = c_to_b_sheet['锦宬半品编码']
        ctb_dict = {}
        for i in range(0, file_length):
            if ctb_c[i] in ctb_dict:
                if ctb_b[i] not in ctb_dict[ctb_c[i]]:
                    ctb_dict[ctb_c[i]].append(ctb_b[i])
            else:
                ctb_dict[ctb_c[i]] = [ctb_b[i]]
        
        # 准备数据
        c_ind = require['锦宬成品料号']
        total = require['合计'].astype('int32')
        
        cc_ind = storage_c['锦宬成品料号'].tolist()
        cc_num = storage_c['当前可用库存']
        
        eb_ind = storage_extra['半品料号'].tolist()
        eb_num = storage_extra['超需求库存']
        
        bb_ind = storage_b['锦宬半品料号'].tolist()
        bb_num = storage_b['半品结余']
        
        file_length = len(require)
        column_names_1 = ['锦宬成品料号', '锦宬半成品料号', '总量']
        column_names_2 = ['锦宬半成品料号', '总量']
        for item in require:
            if isinstance(item, datetime.datetime):
                column_names_1.append(item)
                column_names_2.append(item)
        
        # 计算成品需求
        require_c_dict = []
        used_c_mat_quan = {}
        aggre_b_date = {}
        
        for i in range(0, file_length):
            if total[i] != 0:
                # 库存成品
                cur_cc = 0
                if c_ind[i] in used_c_mat_quan:
                    cur_cc = used_c_mat_quan[c_ind[i]]
                else:
                    num_of_cc = [cc_num[a] for a, x in enumerate(cc_ind) if x == c_ind[i]]
                    if num_of_cc != []:
                        cur_cc = sum(num_of_cc)
                
                c_row = [c_ind[i], ctb_dict[c_ind[i]][0], total[i] - cur_cc]
                day = 0
                for item in require:
                    if isinstance(item, datetime.datetime):
                        entry = require[item][i]
                        # 优先消耗库存成品，并记录成品应制数据
                        if cur_cc >= entry:
                            cur_cc -= entry
                            entry = 0
                        else:
                            entry -= cur_cc
                            cur_cc = 0
                        c_row.append(entry)
                        used_c_mat_quan[c_ind[i]] = cur_cc
                        
                        # 余下应制半品总数
                        for item in ctb_dict[c_ind[i]]:
                            if item not in aggre_b_date:
                                aggre_b_date[item] = []
                            if len(aggre_b_date[item]) <= day:
                                aggre_b_date[item].append(entry)
                            else:
                                aggre_b_date[item][day] += entry
                        
                        day += 1
                if sum(c_row[3:]) != 0:
                    new_sum = sum(c_row[3:])
                    c_row[2] = new_sum
                    require_c_dict.append(c_row)
        
        # 计算半品需求
        require_eb_dict = []
        require_cb_dict = []
        require_b_dict = []
        used_eb_mat_quan = {}
        used_cb_mat_quan = {}
        
        for mat in aggre_b_date:
            cb_row = [mat, sum(aggre_b_date[mat])]
            eb_row = [mat, sum(aggre_b_date[mat])]
            b_row = [mat, sum(aggre_b_date[mat])]
            
            cur_eb = 0
            cur_cb = 0
            
            if mat in used_eb_mat_quan:
                cur_eb = used_eb_mat_quan[mat]
            else:
                num_of_eb = [eb_num[a] for a, x in enumerate(eb_ind) if x == mat]
                cur_eb = sum(num_of_eb)
            
            if mat in used_cb_mat_quan:
                cur_cb = used_cb_mat_quan[mat]
            else:
                num_of_bb = [bb_num[a] for a, x in enumerate(bb_ind) if x == mat]
                cur_cb = sum(num_of_bb)
            
            for b_to_date in aggre_b_date[mat]:
                # 消耗外仓半品
                if cur_eb > 0:
                    if cur_eb >= b_to_date:
                        eb_row.append(b_to_date)
                        cur_eb -= b_to_date
                        b_to_date = 0
                    else:
                        eb_row.append(cur_eb)
                        b_to_date -= cur_eb
                        cur_eb = 0
                else:
                    eb_row.append(0)
                used_eb_mat_quan[mat] = cur_eb
                
                # 消耗库存半品
                if cur_cb > 0:
                    if cur_cb >= b_to_date:
                        cb_row.append(b_to_date)
                        cur_cb -= b_to_date
                        b_to_date = 0
                    else:
                        cb_row.append(cur_cb)
                        b_to_date -= cur_cb
                        cur_cb = 0
                else:
                    cb_row.append(0)
                used_cb_mat_quan[mat] = cur_cb
                
                b_row.append(b_to_date)
            
            if sum(cb_row[2:]) != 0:
                new_sum = sum(cb_row[2:])
                cb_row[1] = new_sum
                require_cb_dict.append(cb_row)
            if sum(b_row[2:]) != 0:
                new_sum = sum(b_row[2:])
                b_row[1] = new_sum
                require_b_dict.append(b_row)
            if sum(eb_row[2:]) != 0:
                new_sum = sum(eb_row[2:])
                eb_row[1] = new_sum
                require_eb_dict.append(eb_row)
        
        # 创建DataFrame并保存
        df_c = pd.DataFrame(require_c_dict, columns=column_names_1)
        df_cb = pd.DataFrame(require_cb_dict, columns=column_names_2)
        df_eb = pd.DataFrame(require_eb_dict, columns=column_names_2)
        df_b = pd.DataFrame(require_b_dict, columns=column_names_2)
        
        # 生成输出文件名
        output_path = os.path.join('temp', '排程结果' + datetime.datetime.now().strftime('%m-%d') + '_' + str(uuid.uuid4())[:8] + '.xlsx')
        
        with pd.ExcelWriter(output_path) as writer:
            df_c.to_excel(writer, '成品需求', index=False)
            df_cb.to_excel(writer, '库存半品出货需求', index=False)
            df_eb.to_excel(writer, '外仓半品出货需求', index=False)
            df_b.to_excel(writer, '半品生产需求', index=False)
        
        return True, "计算完成！", output_path
        
    except Exception as e:
        return False, f"计算失败：{str(e)}", None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
        
        # 检查文件是否上传
        if 'file1' not in request.files or 'file2' not in request.files:
            error_msg = '请上传两个文件！'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        if file1.filename == '' or file2.filename == '':
            error_msg = '请选择两个文件！'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
            error_msg = '只支持Excel文件（.xlsx, .xls）！'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        # 保存上传的文件
        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)
        unique_id = str(uuid.uuid4())[:8]
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_{filename1}')
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_{filename2}')
        
        file1.save(file1_path)
        file2.save(file2_path)
        
        # 第一步：合并需求
        success, message, merged_file_path = merge_requirements(file1_path)
        if not success:
            error_msg = f'合并需求失败：{message}'
            # 清理文件
            if os.path.exists(file1_path):
                os.remove(file1_path)
            if os.path.exists(file2_path):
                os.remove(file2_path)
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        # 第二步：排程计算
        success, message, output_path = calculate_schedule(file1_path, file2_path, merged_file_path)
        
        # 清理临时文件
        if os.path.exists(file1_path):
            os.remove(file1_path)
        if os.path.exists(file2_path):
            os.remove(file2_path)
        if os.path.exists(merged_file_path):
            os.remove(merged_file_path)
        
        if not success:
            error_msg = f'排程计算失败：{message}'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        # 返回结果文件
        return send_file(
            output_path,
            as_attachment=True,
            download_name='排程结果' + datetime.datetime.now().strftime('%m-%d') + '.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        error_msg = f'处理失败：{str(e)}'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
        if is_ajax:
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    # 生产环境使用环境变量PORT，开发环境使用5001
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

