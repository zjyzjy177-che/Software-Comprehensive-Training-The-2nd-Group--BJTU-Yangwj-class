"""
组员C - GUI 登录界面 + 仿真参数配置 + 启动仿真
=================================================
Tkinter 实现：登录验证 → 参数配置 → 调用 main.run_simulation_from_gui → 展示结果

运行方式：
  python gui.py
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import sys
import platform
import threading
import random
import string
import webbrowser

# 必须在任何 matplotlib 导入前设置后端，否则 Tkinter GUI + MacOSX Cocoa 冲突导致动画窗口无法弹出
import matplotlib
matplotlib.use('TkAgg')

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

sys.path.insert(0, os.path.dirname(__file__))

# ====================== 跨平台字体检测 ======================
_OS_SYSTEM = platform.system()
_FONT_CANDIDATES = {
    "Windows": ["微软雅黑", "Microsoft YaHei", "SimHei", "SimSun", "TkDefaultFont"],
    "Darwin": ["PingFang SC", "Heiti SC", "STHeiti", "Apple LiSung", "TkDefaultFont"],
    "Linux": ["WenQuanYi Micro Hei", "Noto Sans CJK SC", "DejaVu Sans", "TkDefaultFont"],
}
_FONT_CANDIDATES_DEFAULT = _FONT_CANDIDATES.get(_OS_SYSTEM, _FONT_CANDIDATES["Linux"])


def _detect_system_font():
    """检测当前系统可用的中文字体，返回字体族名"""
    available = set(tkfont.families())
    for font_name in _FONT_CANDIDATES_DEFAULT:
        if font_name in available:
            return font_name
    return "TkDefaultFont"


SYSTEM_FONT = "TkDefaultFont"  # 初始回退值，Tk root 创建后由 _init_font 更新

# ====================== 常量 ======================
MAX_ATTEMPTS = 5
USER_FILE = os.path.join(os.path.expanduser("~"), ".bjtu_canteen_users.txt")
ILLEGAL_CHARS = set('<>{}[]\\\'\"&|;`$()')
ADMIN_EMAIL = "24281213@bjtu.edu.cn"
SCHOOL_URL = "https://www.bjtu.edu.cn"
HQ_URL = "https://hq.bjtu.edu.cn/index.htm"

# 管理员凭据（无需注册，直接密钥登录）
_ADMINS = {
    "24281213": {"name": "张建宇", "key": "admin1c", "role": "主管理员"},
    "24281210": {"name": "岳思铭", "key": "admin2y", "role": "管理员"},
    "24251293": {"name": "魏嘉昕", "key": "admin3w", "role": "管理员"},
}

# ====================== 多语言翻译表 ======================
LANG_TEXTS = {
    "zh_CN": {
        "window_title": "BJTU 食堂就餐流量仿真系统",
        "system_name": "北京交通大学",
        "subtitle": "食堂就餐流量仿真系统",
        "user_login": "用户登录",
        "role_label": "身份",
        "student": "学生",
        "teacher": "教师",
        "admin": "管理员",
        "admin_key_label": "密  钥",
        "admin_key_empty": "密钥不能为空",
        "admin_key_error": "管理员密钥错误",
        "account_label": "学号/工号",
        "password_label": "密  码",
        "captcha_label": "验证码",
        "login_btn": "本地登录",
        "register_btn": "注册账号",
        "forgot_pwd": "忘记密码？",
        "guest_btn": "访客模式",
        "default_pwd_hint": "默认密码: 学号/工号 + @bjtu",
        "first_login_hint": "!!重要!!：第一次登录请先注册",
        "not_logged_in": "未登录",
        "logged_in": "已登录",
        "status_logged_in": "已登录: {role} | {user}",
        "current_user": "当前用户: {info}",
        "current_user_none": "当前用户: 未登录",
        "logout_btn": "注销",
        "sim_params": "仿真参数设置",
        "ticks_label": "仿真时长 (ticks):",
        "students_label": "学生总数:",
        "canteens_label": "食堂数量:",
        "spawn_label": "生成率 (spawn_rate):",
        "strategy_label": "策略选择",
        "choose_strategy": "选择策略:",
        "weight_label": "权重调节",
        "alpha_label": "α (距离权重):",
        "beta_label": "β (排队权重):",
        "other_label": "其他选项",
        "enable_viz": "启用可视化（弹出 Matplotlib 动画窗口）",
        "browse_config": "浏览配置文件…",
        "launch_btn": "启动仿真",
        "launching": "仿真运行中…",
        "result_label": "仿真结果",
        "running_msg": "正在运行仿真，请稍候…\n",
        "sim_complete": "仿真运行完成",
        "sim_failed": "仿真运行失败",
        "sim_force_stopped": "仿真已被强制停止",
        "stop_btn": "⏹ 强制停止",
        "peak_shift_btn": "错峰对比分析",
        "start_simulation": "启动仿真",
        "stats_title": "【统计数据】",
        "not_login_warn": "未登录",
        "not_login_msg": "请先登录后再启动仿真",
        "param_invalid": "参数无效",
        "select_role_first": "请选择身份（学生/教师）",
        "account_empty": "学号/工号不能为空",
        "password_empty": "密码不能为空",
        "captcha_empty": "验证码不能为空",
        "captcha_error": "验证码错误！请重新输入",
        "input_error": "输入错误",
        "error": "错误",
        "login_failed": "登录失败",
        "account_locked": "该账号登录错误次数已用尽，请联系管理员重置",
        "account_not_registered": "账号未注册！\n请先点击「注册账号」进行注册\n默认密码：学号/工号 + @bjtu",
        "login_success": "登录成功",
        "welcome": "欢迎，{role} {account}！",
        "pw_error_msg": "账号或密码错误！\n剩余尝试次数：{remaining}",
        "pw_locked_msg": "\n\n该账号已被锁定，请联系管理员重置",
        "forgot_title": "忘记密码",
        "forgot_msg": "请联系管理员重置密码\n\n管理员邮箱：{email}\n\n或重新注册账号",
        "register_title": "账号注册",
        "register_prompt": "请输入{role}学号/工号：",
        "register_failed": "注册失败",
        "register_exists": "该账号已注册！如需重置密码请联系管理员",
        "register_success": "注册成功",
        "register_done": "注册完成！\n\n身份：{role}\n账号：{uid}\n默认密码：{pwd}",
        "config_loaded": "已从配置文件加载参数:\n{file}",
        "load_success": "加载成功",
        "load_failed": "加载失败",
        "config_parse_error": "配置文件解析失败:\n{e}",
        "select_config": "选择配置文件",
        "json_files": "JSON 文件",
        "all_files": "所有文件",
        "friendly_links": "友情链接",
        "click_me": "点击我Click Me Now!",
        "lang_label": "语言",
        "prompt": "提示",
        "ticks_must_int": "ticks 必须是整数",
        "ticks_must_positive": "ticks 必须大于 0",
        "students_must_int": "学生数必须是整数",
        "students_not_negative": "学生数不能为负数",
        "canteens_must_int": "食堂数必须是整数",
        "canteens_must_positive": "食堂数必须大于 0",
        "spawn_must_number": "spawn_rate 必须是数字",
        "spawn_range": "spawn_rate 必须在 [0, 1] 之间",
        "viz_window_title": "BJTU食堂就餐流量仿真",
        "viz_map_title": "学生移动与食堂分布",
        "viz_xlabel": "X坐标 (米)",
        "viz_ylabel": "Y坐标 (米)",
        "viz_stats_title": "排队人数变化曲线",
        "viz_stats_xlabel": "仿真周期",
        "viz_stats_ylabel": "排队人数",
        "viz_pie_title": "学生状态分布",
        "viz_info_loading": "仿真信息加载中...",
        "viz_walking": "行走",
        "viz_queuing": "排队",
        "viz_eating": "用餐",
        "viz_leaving": "离开",
        "viz_canteen": "食堂",
        "viz_status": "动画状态: {status}",
        "viz_speed": "动画速度: {speed}ms",
        "viz_reset": "视图已重置",
        "limit_warn_title": "参数上限警告",
        "limit_warn_msg": "以下参数超过建议上限，可能导致卡顿或崩溃：",
        "limit_warn_confirm": "确定要继续吗？",
        "no_canteen": "请至少勾选一个开放的食堂",
        "export_title": "导出仿真报告",
        "export_success": "已导出到:",
        "success": "成功",
        "save_settings_title": "仿真保存设置",
        "export_select_format": "选择导出格式：",
        "export_save_path": "保存位置：",
        "export_browse": "浏览...",
        "export_btn": "导出",
        "cancel": "取消",
        "save_auto_save": "仿真完成后自动保存结果",
        "save_format": "保存格式：",
        "save_path_label": "保存路径：",
        "save_browse": "浏览",
        "save_launch": "启动仿真",
        "start_time_label": "仿真开始时间:",
        "open_canteens_label": "开放食堂:",
        "start_time_invalid": "开始时间格式错误，请使用 HH:MM 格式（如 07:00）",
        "start_time_range": "开始时间超出范围（00:00-23:59）",
        "stagger_toggle": "午间错峰下课（12:00→12:20 分批）",
    },
    "zh_TW": {
        "window_title": "BJTU 食堂就餐流量模擬系統",
        "system_name": "北京交通大學",
        "subtitle": "食堂就餐流量模擬系統",
        "user_login": "用戶登錄",
        "role_label": "身份",
        "student": "學生",
        "teacher": "教師",
        "admin": "管理員",
        "admin_key_label": "密  鑰",
        "admin_key_empty": "密鑰不能為空",
        "admin_key_error": "管理員密鑰錯誤",
        "account_label": "學號/工號",
        "password_label": "密  碼",
        "captcha_label": "驗證碼",
        "login_btn": "本地登錄",
        "register_btn": "註冊賬號",
        "forgot_pwd": "忘記密碼？",
        "guest_btn": "訪客模式",
        "default_pwd_hint": "默認密碼: 學號/工號 + @bjtu",
        "first_login_hint": "!!重要!!：第一次登錄請先註冊",
        "not_logged_in": "未登錄",
        "logged_in": "已登錄",
        "status_logged_in": "已登錄: {role} | {user}",
        "current_user": "當前用戶: {info}",
        "current_user_none": "當前用戶: 未登錄",
        "logout_btn": "登出",
        "sim_params": "模擬參數設置",
        "ticks_label": "模擬時長 (ticks):",
        "students_label": "學生總數:",
        "canteens_label": "食堂數量:",
        "spawn_label": "生成率 (spawn_rate):",
        "strategy_label": "策略選擇",
        "choose_strategy": "選擇策略:",
        "weight_label": "權重調節",
        "alpha_label": "α (距離權重):",
        "beta_label": "β (排隊權重):",
        "other_label": "其他選項",
        "enable_viz": "啟用視覺化（彈出 Matplotlib 動畫窗口）",
        "browse_config": "瀏覽配置文件…",
        "launch_btn": "啟動模擬",
        "launching": "模擬運行中…",
        "result_label": "模擬結果",
        "running_msg": "正在運行模擬，請稍候…\n",
        "sim_complete": "模擬運行完成",
        "sim_failed": "模擬運行失敗",
        "sim_force_stopped": "模擬已被強制停止",
        "stop_btn": "⏹ 強制停止",
        "peak_shift_btn": "錯峰對比分析",
        "start_simulation": "啟動模擬",
        "stats_title": "【統計數據】",
        "not_login_warn": "未登錄",
        "not_login_msg": "請先登錄後再啟動模擬",
        "param_invalid": "參數無效",
        "select_role_first": "請選擇身份（學生/教師）",
        "account_empty": "學號/工號不能為空",
        "password_empty": "密碼不能為空",
        "captcha_empty": "驗證碼不能為空",
        "captcha_error": "驗證碼錯誤！請重新輸入",
        "input_error": "輸入錯誤",
        "error": "錯誤",
        "login_failed": "登錄失敗",
        "account_locked": "該賬號登錄錯誤次數已用盡，請聯繫管理員重置",
        "account_not_registered": "賬號未註冊！\n請先點擊「註冊賬號」進行註冊\n默認密碼：學號/工號 + @bjtu",
        "login_success": "登錄成功",
        "welcome": "歡迎，{role} {account}！",
        "pw_error_msg": "賬號或密碼錯誤！\n剩餘嘗試次數：{remaining}",
        "pw_locked_msg": "\n\n該賬號已被鎖定，請聯繫管理員重置",
        "forgot_title": "忘記密碼",
        "forgot_msg": "請聯繫管理員重置密碼\n\n管理員郵箱：{email}\n\n或重新註冊賬號",
        "register_title": "賬號註冊",
        "register_prompt": "請輸入{role}學號/工號：",
        "register_failed": "註冊失敗",
        "register_exists": "該賬號已註冊！如需重置密碼請聯繫管理員",
        "register_success": "註冊成功",
        "register_done": "註冊完成！\n\n身份：{role}\n賬號：{uid}\n默認密碼：{pwd}",
        "config_loaded": "已從配置文件加載參數:\n{file}",
        "load_success": "加載成功",
        "load_failed": "加載失敗",
        "config_parse_error": "配置文件解析失敗:\n{e}",
        "select_config": "選擇配置文件",
        "json_files": "JSON 文件",
        "all_files": "所有文件",
        "friendly_links": "友情鏈接",
        "click_me": "點擊我Click Me Now!",
        "lang_label": "語言",
        "prompt": "提示",
        "ticks_must_int": "ticks 必須是整數",
        "ticks_must_positive": "ticks 必須大於 0",
        "students_must_int": "學生數必須是整數",
        "students_not_negative": "學生數不能為負數",
        "canteens_must_int": "食堂數必須是整數",
        "canteens_must_positive": "食堂數必須大於 0",
        "spawn_must_number": "spawn_rate 必須是數字",
        "spawn_range": "spawn_rate 必須在 [0, 1] 之間",
        "viz_window_title": "BJTU食堂就餐流量模擬",
        "viz_map_title": "學生移動與食堂分佈",
        "viz_xlabel": "X坐標 (米)",
        "viz_ylabel": "Y坐標 (米)",
        "viz_stats_title": "排隊人數變化曲線",
        "viz_stats_xlabel": "模擬週期",
        "viz_stats_ylabel": "排隊人數",
        "viz_pie_title": "學生狀態分佈",
        "viz_info_loading": "模擬信息加載中...",
        "viz_walking": "行走",
        "viz_queuing": "排隊",
        "viz_eating": "用餐",
        "viz_leaving": "離開",
        "viz_canteen": "食堂",
        "viz_status": "動畫狀態: {status}",
        "viz_speed": "動畫速度: {speed}ms",
        "viz_reset": "視圖已重置",
        "limit_warn_title": "參數上限警告",
        "limit_warn_msg": "以下參數超過建議上限，可能導致卡頓或崩潰：",
        "limit_warn_confirm": "確定要繼續嗎？",
        "no_canteen": "請至少勾選一個開放的食堂",
        "export_title": "導出模擬報告",
        "export_success": "已導出到:",
        "success": "成功",
        "save_settings_title": "模擬保存設置",
        "export_select_format": "選擇導出格式：",
        "export_save_path": "保存位置：",
        "export_browse": "瀏覽...",
        "export_btn": "導出",
        "cancel": "取消",
        "save_auto_save": "模擬完成後自動保存結果",
        "save_format": "保存格式：",
        "save_path_label": "保存路徑：",
        "save_browse": "瀏覽",
        "save_launch": "啟動模擬",
        "start_time_label": "模擬開始時間:",
        "open_canteens_label": "開放食堂:",
        "start_time_invalid": "開始時間格式錯誤，請使用 HH:MM 格式（如 07:00）",
        "start_time_range": "開始時間超出範圍（00:00-23:59）",
        "stagger_toggle": "午間錯峰下課（12:00→12:20 分批）",
    },
    "en": {
        "window_title": "BJTU Canteen Dining Flow Simulation System",
        "system_name": "Beijing Jiaotong University",
        "subtitle": "Canteen Dining Flow Simulation System",
        "user_login": "User Login",
        "role_label": "Role",
        "student": "Student",
        "teacher": "Teacher",
        "admin": "Admin",
        "admin_key_label": "Key",
        "admin_key_empty": "Key cannot be empty",
        "admin_key_error": "Invalid admin key",
        "account_label": "ID",
        "password_label": "Password",
        "captcha_label": "Captcha",
        "login_btn": "Login",
        "register_btn": "Register",
        "forgot_pwd": "Forgot Password?",
        "guest_btn": "Guest Mode",
        "default_pwd_hint": "Default password: ID + @bjtu",
        "first_login_hint": "IMPORTANT: First-time users must register first",
        "not_logged_in": "Not logged in",
        "logged_in": "Logged in",
        "status_logged_in": "Logged in: {role} | {user}",
        "current_user": "Current User: {info}",
        "current_user_none": "Current User: None",
        "logout_btn": "Logout",
        "sim_params": "Simulation Parameters",
        "ticks_label": "Duration (ticks):",
        "students_label": "Student Count:",
        "canteens_label": "Canteen Count:",
        "spawn_label": "Spawn Rate:",
        "strategy_label": "Strategy Selection",
        "choose_strategy": "Strategy:",
        "weight_label": "Weight Adjustment",
        "alpha_label": "α (Distance):",
        "beta_label": "β (Queue):",
        "other_label": "Other Options",
        "enable_viz": "Enable Visualization (Matplotlib Animation Window)",
        "browse_config": "Browse Config…",
        "launch_btn": "Launch Simulation",
        "launching": "Simulation Running…",
        "result_label": "Simulation Results",
        "running_msg": "Running simulation, please wait…\n",
        "sim_complete": "Simulation Complete",
        "sim_failed": "Simulation Failed",
        "sim_force_stopped": "Simulation force stopped",
        "stop_btn": "⏹ Force Stop",
        "peak_shift_btn": "Peak Shift Comparison",
        "start_simulation": "Launch Simulation",
        "stats_title": "[Statistics]",
        "not_login_warn": "Not Logged In",
        "not_login_msg": "Please login before launching simulation",
        "param_invalid": "Invalid Parameters",
        "select_role_first": "Please select a role (Student/Teacher)",
        "account_empty": "ID cannot be empty",
        "password_empty": "Password cannot be empty",
        "captcha_empty": "Captcha cannot be empty",
        "captcha_error": "Incorrect captcha! Please re-enter",
        "input_error": "Input Error",
        "error": "Error",
        "login_failed": "Login Failed",
        "account_locked": "Account locked due to too many failed attempts. Contact admin to reset.",
        "account_not_registered": "Account not registered!\nPlease click [Register] first\nDefault password: ID + @bjtu",
        "login_success": "Login Successful",
        "welcome": "Welcome, {role} {account}!",
        "pw_error_msg": "Incorrect ID or password!\nRemaining attempts: {remaining}",
        "pw_locked_msg": "\n\nThis account has been locked. Contact admin to reset.",
        "forgot_title": "Forgot Password",
        "forgot_msg": "Contact admin to reset password\n\nAdmin email: {email}\n\nOr re-register",
        "register_title": "Account Registration",
        "register_prompt": "Enter {role} ID:",
        "register_failed": "Registration Failed",
        "register_exists": "Account already exists! Contact admin to reset password.",
        "register_success": "Registration Successful",
        "register_done": "Registration complete!\n\nRole: {role}\nID: {uid}\nDefault password: {pwd}",
        "config_loaded": "Configuration loaded from:\n{file}",
        "load_success": "Load Successful",
        "load_failed": "Load Failed",
        "config_parse_error": "Config file parse error:\n{e}",
        "select_config": "Select Configuration File",
        "json_files": "JSON Files",
        "all_files": "All Files",
        "friendly_links": "Friendly Links",
        "click_me": "Click Me Now!",
        "lang_label": "Lang",
        "prompt": "Notice",
        "ticks_must_int": "ticks must be an integer",
        "ticks_must_positive": "ticks must be greater than 0",
        "students_must_int": "student count must be an integer",
        "students_not_negative": "student count cannot be negative",
        "canteens_must_int": "canteen count must be an integer",
        "canteens_must_positive": "canteen count must be greater than 0",
        "spawn_must_number": "spawn_rate must be a number",
        "spawn_range": "spawn_rate must be in [0, 1]",
        "viz_window_title": "BJTU Canteen Dining Flow Simulation",
        "viz_map_title": "Student Movement & Canteen Distribution",
        "viz_xlabel": "X Coordinate (m)",
        "viz_ylabel": "Y Coordinate (m)",
        "viz_stats_title": "Queue Length Over Time",
        "viz_stats_xlabel": "Simulation Tick",
        "viz_stats_ylabel": "Queue Length",
        "viz_pie_title": "Student Status Distribution",
        "viz_info_loading": "Loading simulation info...",
        "viz_walking": "Walking",
        "viz_queuing": "Queuing",
        "viz_eating": "Eating",
        "viz_leaving": "Leaving",
        "viz_canteen": "Canteen",
        "viz_status": "Animation Status: {status}",
        "viz_speed": "Animation Speed: {speed}ms",
        "viz_reset": "View Reset",
        "limit_warn_title": "Parameter Limit Warning",
        "limit_warn_msg": "The following parameters exceed recommended limits and may cause lag or crash:",
        "limit_warn_confirm": "Continue anyway?",
        "no_canteen": "Please select at least one canteen",
        "export_title": "Export Simulation Report",
        "export_success": "Exported to:",
        "success": "Success",
        "save_settings_title": "Simulation Save Settings",
        "export_select_format": "Select Format:",
        "export_save_path": "Save To:",
        "export_browse": "Browse...",
        "export_btn": "Export",
        "cancel": "Cancel",
        "save_auto_save": "Auto-save results after simulation",
        "save_format": "Format:",
        "save_path_label": "Save Path:",
        "save_browse": "Browse",
        "save_launch": "Launch",
        "start_time_label": "Start Time:",
        "open_canteens_label": "Open Canteens:",
        "start_time_invalid": "Invalid time format, use HH:MM (e.g. 07:00)",
        "start_time_range": "Time out of range (00:00-23:59)",
        "stagger_toggle": "Stagger Lunch Peak (12:00→12:20 batches)",
    },
}


# ====================== 纯函数（不依赖 Tk） ======================
def init_user_file():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            f.write("")


def load_users():
    users = {}
    init_user_file()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    role, uid, pwd = parts[0], parts[1], parts[2]
                    users[f"{role}:{uid}"] = pwd
    return users


def save_user(role, uid, pwd):
    users = load_users()
    users[f"{role}:{uid}"] = pwd
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for k, v in users.items():
            r, u = k.split(":", 1)
            f.write(f"{r}|{u}|{v}\n")


def get_default_password(uid):
    return f"{uid}@bjtu"


def validate_account(account, role):
    """按角色校验账号格式：学生学号8位数字，教师工号4-5位数字"""
    if not account or not account.strip():
        return False, "账号不能为空"
    account = account.strip()
    if any(c in ILLEGAL_CHARS for c in account):
        return False, "账号包含非法字符"
    if not account.isdigit():
        return False, "账号必须为纯数字"
    if role in ("student", "学生", "學生"):
        if len(account) != 8:
            return False, "学生学号必须为8位数字"
    elif role in ("teacher", "教师", "教師"):
        if not (4 <= len(account) <= 5):
            return False, "教师工号必须为4-5位数字"
    return True, account


def validate_password(password):
    if not password:
        return False, "密码不能为空"
    if len(password) < 3:
        return False, "密码长度至少3位"
    return True, password


# ====================== ToolTip 悬停提示 ======================
class ToolTip:
    """鼠标悬停时在 ? 图标旁弹出参数说明，text 可为可调用对象以支持语言切换"""
    def __init__(self, widget, text):
        self.widget = widget
        self._text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _get_text(self):
        if callable(self._text):
            return self._text()
        return self._text

    def _show(self, event=None):
        if self.tip_window:
            return
        text = self._get_text()
        if not text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify="left",
                         background="#ffffcc", foreground="#333333",
                         font=(SYSTEM_FONT, 9), relief="solid", borderwidth=1,
                         padx=8, pady=4, wraplength=320)
        label.pack()

    def _hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ====================== 参数提示文本（三语） ======================
_PARAM_TOOLTIPS = {
    "zh_CN": {
        "ticks": "仿真时长（周期数）\n• 一个 tick 模拟若干秒\n• 建议范围：50-1000\n• ⚠ 超过 5000 可能明显卡顿",
        "students": "初始学生数量\n• 影响排队压力和运算量\n• 建议范围：10-500\n• ⚠ 超过 2000 可能卡顿（取决于电脑性能）",
        "canteens": "食堂数量\n• 每个食堂有独立窗口和容量\n• 建议范围：1-6\n• ⚠ 超过 10 个食堂动画信息面板会截断显示",
        "spawn": "学生生成速率（0-1）\n• 每个 tick 生成新学生的概率\n• 建议范围：0.01-0.3\n• 0 = 不生成新学生，仅用初始学生",
        "strategy": "食堂选择策略\n• distance：优先选最近食堂\n• queue：优先选排队最短食堂\n• balanced：综合距离和排队人数",
        "alpha": "距离权重（α）\n• 值越大 → 学生越倾向去近的食堂\n• 建议：高峰 0.3，平峰 0.8",
        "beta": "排队人数权重（β）\n• 值越大 → 学生越倾向去人少的食堂\n• 建议：高峰 0.7，平峰 0.2",
        "viz": "启用后弹出 Matplotlib 动画窗口\n• 实时显示学生移动和食堂排队\n• 注意：学生数 > 500 时动画可能卡顿\n• 空格暂停，↑↓ 调速，R 重置视图",
        "peak": "错峰下课方案对比分析\n• 对比 0/5/10/15/20/30 分钟错峰效果\n• 生成四图对比 + 文本摘要\n• 排队峰值降低越多 = 错峰效果越好",
        "start_time": "仿真开始时钟时间 (HH:MM)\n• 例如 07:00 或 11:30\n• 钟表从此时间开始计时\n• 课表事件按此时间触发",
    },
    "zh_TW": {
        "ticks": "模擬時長（週期數）\n• 一個 tick 模擬若干秒\n• 建議範圍：50-1000\n• ⚠ 超過 5000 可能明顯卡頓",
        "students": "初始學生數量\n• 影響排隊壓力和運算量\n• 建議範圍：10-500\n• ⚠ 超過 2000 可能卡頓（取決於電腦性能）",
        "canteens": "食堂數量\n• 每個食堂有獨立窗口和容量\n• 建議範圍：1-6\n• ⚠ 超過 10 個食堂動畫資訊面板會截斷顯示",
        "spawn": "學生生成速率（0-1）\n• 每個 tick 生成新學生的機率\n• 建議範圍：0.01-0.3\n• 0 = 不生成新學生，僅用初始學生",
        "strategy": "食堂選擇策略\n• distance：優先選最近食堂\n• queue：優先選排隊最短食堂\n• balanced：綜合距離和排隊人數",
        "alpha": "距離權重（α）\n• 值越大 → 學生越傾向去近的食堂\n• 建議：高峰 0.3，平峰 0.8",
        "beta": "排隊人數權重（β）\n• 值越大 → 學生越傾向去人少的食堂\n• 建議：高峰 0.7，平峰 0.2",
        "viz": "啟用後彈出 Matplotlib 動畫窗口\n• 即時顯示學生移動和食堂排隊\n• 注意：學生數 > 500 時動畫可能卡頓\n• 空格暫停，↑↓ 調速，R 重置視圖",
        "peak": "錯峰下課方案對比分析\n• 對比 0/5/10/15/20/30 分鐘錯峰效果\n• 生成四圖對比 + 文本摘要\n• 排隊峰值降低越多 = 錯峰效果越好",
        "start_time": "模擬開始時鐘時間 (HH:MM)\n• 例如 07:00 或 11:30\n• 時鐘從此時間開始計時\n• 課表事件按此時間觸發",
    },
    "en": {
        "ticks": "Simulation duration (ticks)\n• One tick ≈ several seconds\n• Suggested: 50-1000\n• ⚠ > 5000 may cause lag",
        "students": "Initial student count\n• Affects queue pressure & computation\n• Suggested: 10-500\n• ⚠ > 2000 may cause lag",
        "canteens": "Number of canteens\n• Each has independent windows & capacity\n• Suggested: 1-6\n• ⚠ > 10 will truncate info panel",
        "spawn": "Student spawn rate (0-1)\n• Probability of new student per tick\n• Suggested: 0.01-0.3\n• 0 = no new students, initial only",
        "strategy": "Canteen selection strategy\n• distance: prefer nearest canteen\n• queue: prefer shortest queue\n• balanced: combine distance & queue",
        "alpha": "Distance weight (α)\n• Higher → students go to nearer canteen\n• Suggest: peak hours 0.3, off-peak 0.8",
        "beta": "Queue weight (β)\n• Higher → students avoid crowded canteens\n• Suggest: peak hours 0.7, off-peak 0.2",
        "viz": "Enable Matplotlib animation window\n• Real-time student movement & queues\n• Note: > 500 students may lag\n• Space=pause, ↑↓=speed, R=reset",
        "peak": "Peak shift comparison analysis\n• Compare 0/5/10/15/20/30 min stagger\n• Generates 4-chart comparison + summary\n• Higher queue reduction = better stagger",
        "start_time": "Simulation start time (HH:MM)\n• e.g. 07:00 or 11:30\n• Clock starts counting from this time\n• Schedule events trigger accordingly",
    },
}

def _get_tooltip(key, lang):
    """获取指定语言的 ToolTip 文本"""
    return _PARAM_TOOLTIPS.get(lang, _PARAM_TOOLTIPS["zh_CN"]).get(key, "")

# 参数上限建议
_PARAM_LIMITS = {"ticks": 5000, "students": 2000, "canteens": 15, "spawn": 1.0}
_PARAM_LIMIT_WARNINGS = {
    "zh_CN": {
        "ticks": "ticks 超过 5000 可能导致仿真运行缓慢或卡顿",
        "students": "学生数超过 2000 可能导致仿真和动画严重卡顿",
        "canteens": "食堂数超过 15 个，信息面板可能显示不全",
    },
    "zh_TW": {
        "ticks": "ticks 超過 5000 可能導致模擬運行緩慢或卡頓",
        "students": "學生數超過 2000 可能導致模擬和動畫嚴重卡頓",
        "canteens": "食堂數超過 15 個，資訊面板可能顯示不全",
    },
    "en": {
        "ticks": "ticks > 5000 may cause slow simulation or lag",
        "students": "Students > 2000 may cause severe simulation/animation lag",
        "canteens": "Canteens > 15 may overflow the info panel",
    },
}


# ====================== GUI 主类 ======================
class BJTUSimulationGUI:
    def __init__(self):
        self.login_attempts = {}
        self.current_user = None
        self.current_role = None
        self.captcha_code = ""
        self.lang = "zh_CN"
        self._flash_job = None
        self._config_data = None
        self._auto_save_settings = None  # 自动保存设置
        self._peak_stop_requested = False  # 错峰对比中断标志

        # 先创建 root 以便 _detect_system_font 可用
        self.root = tk.Tk()
        global SYSTEM_FONT
        SYSTEM_FONT = _detect_system_font()
        # ttk 现代主题
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TButton', font=(SYSTEM_FONT, 10), padding=6)
        style.configure('TCombobox', font=(SYSTEM_FONT, 10))
        style.configure('TLabel', font=(SYSTEM_FONT, 10))

        self._build_ui()
        self._generate_captcha()

    # ---------- 颜色方案（宝蓝色） ----------
    BLUE = "#2260d6"
    BLUE_DARK = "#173f8a"
    BLUE_LIGHT = "#e8f0fe"
    WHITE = "#ffffff"
    BG = "#dce5f5"
    TEXT = "#333333"
    HINT = "#999999"
    BORDER = "#dcdfe6"
    BLUE_HOVER = "#1a4db3"
    YELLOW_FLASH = "#ffdd00"
    RED_CLICK = "#dd0000"

    def t(self, key, **kwargs):
        text = LANG_TEXTS.get(self.lang, LANG_TEXTS["zh_CN"]).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text

    # ---------- UI 构建 ----------
    def _build_ui(self):
        self.root.title(self.t("window_title"))
        self.root.geometry("600x740")
        self.root.resizable(True, True)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 600) // 2
        y = (sh - 740) // 2
        self.root.geometry(f"600x740+{x}+{y}")
        self.root.config(bg=self.BG)

        self.root.bind("<Return>", lambda e: self._local_login())

        self._build_login_frame()
        self._build_config_frame()

        self.status_bar = tk.Label(self.root, text=self.t("not_logged_in"), font=(SYSTEM_FONT, 8),
                                   bg=self.BLUE, fg=self.WHITE, anchor="w", padx=10)
        self.status_bar.pack(side="bottom", fill="x")

        self.copyright_bar = tk.Label(self.root,
            text="Copyright © 2026 BJTU软件综合实训2026春杨武杰班级第 2 小组 版权所有",
            font=(SYSTEM_FONT, 7), bg=self.BG, fg=self.BLUE_DARK, anchor="center")
        self.copyright_bar.pack(side="bottom", fill="x", pady=(0, 2))

        self._start_flash()

    def _build_login_frame(self):
        self.login_frame = tk.Frame(self.root, bg=self.BG)
        self.login_frame.pack(fill="both", expand=True)

        # ---- 蓝色顶部条（含校徽） ----
        header = tk.Frame(self.login_frame, bg=self.BLUE, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "school_logo.png")
        self.logo_img = None
        if HAS_PIL and os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((68, 68), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                logo_label = tk.Label(header, image=self.logo_img, bg=self.BLUE)
                logo_label.pack(side="left", padx=(15, 10), pady=11)
            except Exception:
                pass  # 图片损坏或格式不支持时静默跳过

        text_frame = tk.Frame(header, bg=self.BLUE)
        text_frame.pack(side="left", fill="both", expand=True)
        self.lbl_sys_name = tk.Label(text_frame, text=self.t("system_name"),
                                     font=(SYSTEM_FONT, 20, "bold"),
                                     bg=self.BLUE, fg=self.WHITE)
        self.lbl_sys_name.pack(anchor="w", pady=(16, 0))
        self.lbl_subtitle = tk.Label(text_frame, text=self.t("subtitle"),
                                     font=(SYSTEM_FONT, 11),
                                     bg=self.BLUE, fg=self.BLUE_LIGHT)
        self.lbl_subtitle.pack(anchor="w")

        # 语言切换按钮（右上角）
        lang_frame = tk.Frame(header, bg=self.BLUE)
        lang_frame.pack(side="right", padx=(0, 10), pady=(8, 0))
        tk.Label(lang_frame, text=self.t("lang_label") + ":", font=(SYSTEM_FONT, 8),
                 bg=self.BLUE, fg=self.BLUE_LIGHT).pack(side="left", padx=(0, 4))
        self._lang_btns = {}
        for code, label in [("zh_CN", "简"), ("zh_TW", "繁"), ("en", "EN")]:
            frame = tk.Frame(lang_frame, bg=self.BLUE_DARK, cursor="hand2",
                             relief="flat", bd=0, highlightbackground=self.BLUE_DARK)
            lbl = tk.Label(frame, text=label, font=(SYSTEM_FONT, 7),
                          bg=self.BLUE_DARK, fg=self.WHITE)
            lbl.pack(padx=4, pady=1)
            for w in (frame, lbl):
                w.bind("<Button-1>", lambda e, c=code: self._switch_lang(c))
            frame.pack(side="left", padx=1)
            self._lang_btns[code] = (frame, lbl)
        self._set_lang_btn_style("zh_CN", self.BLUE_HOVER)

        # ---- 白色登录卡片（居中） ----
        card_wrapper = tk.Frame(self.login_frame, bg=self.BG)
        card_wrapper.pack(fill="x", pady=(15, 0))
        card = tk.Frame(card_wrapper, bg=self.WHITE, relief="solid", bd=1, width=440, height=430)
        card.pack()
        card.pack_propagate(False)

        # 卡片标题行（标题居中 + 管理员按钮居右）
        title_row = tk.Frame(card, bg=self.WHITE)
        title_row.pack(fill="x", pady=(18, 12), padx=20)

        self.lbl_card_title = tk.Label(title_row, text=self.t("user_login"),
                                       font=(SYSTEM_FONT, 15, "bold"),
                                       bg=self.WHITE, fg=self.BLUE_DARK)
        self.lbl_card_title.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_admin = self._make_btn(title_row, self.t("admin") + "?",
                                        font=(SYSTEM_FONT, 9, "bold"),
                                        bg="#CC0000", fg="#FFD700",
                                        active_bg="#990000", active_fg="#FFD700",
                                        command=self._admin_login,
                                        padx=10, pady=2)
        self.btn_admin.pack(side="right")

        # ---- 表单区域 ----
        form = tk.Frame(card, bg=self.WHITE)
        form.pack()

        # 角色选择
        self.lbl_role = tk.Label(form, text=self.t("role_label"), font=(SYSTEM_FONT, 11),
                                 bg=self.WHITE, fg=self.TEXT)
        self.lbl_role.grid(row=0, column=0, padx=(0, 10), pady=8, sticky="e")
        self.role_var = tk.StringVar(value="")
        self.role_var.trace_add("write", self._on_role_change)
        rf = tk.Frame(form, bg=self.WHITE)
        rf.grid(row=0, column=1, sticky="w", pady=8)
        self._role_buttons = []
        for val_key in ["student", "teacher"]:
            val_display = self.t(val_key)
            rb = tk.Radiobutton(rf, text=val_display, variable=self.role_var, value=val_key,
                                font=(SYSTEM_FONT, 11), bg=self.WHITE,
                                activebackground=self.WHITE,
                                selectcolor=self.WHITE,
                                fg=self.TEXT)
            rb.pack(side="left", padx=(0, 15))
            self._role_buttons.append(rb)
        for rb in self._role_buttons:
            rb.deselect()
        self.root.update_idletasks()

        # 账号
        self.lbl_account = tk.Label(form, text=self.t("account_label"), font=(SYSTEM_FONT, 11),
                                    bg=self.WHITE, fg=self.TEXT)
        self.lbl_account.grid(row=1, column=0, padx=(0, 10), pady=6, sticky="e")
        self.entry_account = tk.Entry(form, font=(SYSTEM_FONT, 11), width=22,
                                      relief="solid", bd=1, highlightthickness=0)
        self.entry_account.grid(row=1, column=1, pady=6, sticky="w")
        self._style_entry(self.entry_account)

        # 密码
        self.lbl_password = tk.Label(form, text=self.t("password_label"), font=(SYSTEM_FONT, 11),
                                     bg=self.WHITE, fg=self.TEXT)
        self.lbl_password.grid(row=2, column=0, padx=(0, 10), pady=6, sticky="e")
        self.entry_password = tk.Entry(form, font=(SYSTEM_FONT, 11), width=22,
                                       relief="solid", bd=1, show="*", highlightthickness=0)
        self.entry_password.grid(row=2, column=1, pady=6, sticky="w")
        self._style_entry(self.entry_password)

        # 验证码
        self.lbl_captcha = tk.Label(form, text=self.t("captcha_label"), font=(SYSTEM_FONT, 11),
                                    bg=self.WHITE, fg=self.TEXT)
        self.lbl_captcha.grid(row=3, column=0, padx=(0, 10), pady=6, sticky="e")
        captcha_row = tk.Frame(form, bg=self.WHITE)
        captcha_row.grid(row=3, column=1, pady=6, sticky="w")
        self.entry_captcha = tk.Entry(captcha_row, font=(SYSTEM_FONT, 11), width=10,
                                      relief="solid", bd=1, highlightthickness=0)
        self.entry_captcha.pack(side="left")
        self._style_entry(self.entry_captcha)

        self.captcha_canvas = tk.Canvas(captcha_row, width=110, height=34,
                                        relief="solid", bd=1, cursor="hand2",
                                        bg=self.WHITE, highlightthickness=0)
        self.captcha_canvas.pack(side="left", padx=(8, 0))
        self.captcha_canvas.bind("<Button-1>", lambda e: self._generate_captcha())

        # ---- 登录按钮 ----
        btn_row = tk.Frame(card, bg=self.WHITE)
        btn_row.pack(pady=(14, 4))

        self.btn_local = self._make_btn(btn_row, self.t("login_btn"),
                                         font=(SYSTEM_FONT, 11, "bold"),
                                         bg=self.BLUE, fg=self.WHITE,
                                         active_bg=self.BLUE_HOVER, active_fg=self.WHITE,
                                         command=self._local_login,
                                         width=12, padx=10, pady=4,
                                         pack_side="left", pack_padx=5)

        # ---- 底部链接 ----
        link_row = tk.Frame(card, bg=self.WHITE)
        link_row.pack(pady=(6, 2))

        self.btn_register = tk.Button(link_row, text=self.t("register_btn"), command=self._register,
                                      font=(SYSTEM_FONT, 9), bg=self.WHITE, fg=self.BLUE,
                                      relief="flat", bd=0, cursor="hand2")
        self.btn_register.pack(side="left", padx=6)

        self.lbl_forget = tk.Label(link_row, text=self.t("forgot_pwd"),
                                   font=(SYSTEM_FONT, 9, "underline"),
                                   fg=self.BLUE, bg=self.WHITE, cursor="hand2")
        self.lbl_forget.pack(side="left", padx=6)
        self.lbl_forget.bind("<Button-1>", lambda e: self._forgot_password())

        self.btn_guest = tk.Button(link_row, text=self.t("guest_btn"), command=self._guest_login,
                                   font=(SYSTEM_FONT, 9), bg=self.WHITE, fg=self.BLUE,
                                   relief="flat", bd=0, cursor="hand2")
        self.btn_guest.pack(side="left", padx=6)

        self.lbl_pwd_hint = tk.Label(card, text=self.t("default_pwd_hint"),
                                     font=(SYSTEM_FONT, 8), fg=self.HINT, bg=self.WHITE)
        self.lbl_pwd_hint.pack(pady=(8, 0))

        self.lbl_first_login = tk.Label(card, text=self.t("first_login_hint"),
                                        font=(SYSTEM_FONT, 8, "bold"), fg="#dd0000", bg=self.WHITE)
        self.lbl_first_login.pack(pady=(4, 14))

        # ---- 四张图片（排在登录卡片下方，图片缺失时自动隐藏） ----
        self._pic_labels = []
        if HAS_PIL:
            pic_frame = tk.Frame(self.login_frame, bg=self.BG)
            has_any = False
            for i in range(1, 5):
                pic_path = os.path.join(os.path.dirname(__file__), "assets", f"picture{i}.png")
                if os.path.exists(pic_path):
                    try:
                        img = Image.open(pic_path)
                        img = img.resize((120, 90), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        lbl = tk.Label(pic_frame, image=photo, bg=self.WHITE, relief="solid", bd=1)
                        lbl.image = photo
                        lbl.pack(side="left", padx=4)
                        self._pic_labels.append(lbl)
                        has_any = True
                    except Exception:
                        pass
            if has_any:
                pic_frame.pack(pady=(15, 6))

        # ---- 友情链接（闪烁动画） ----
        link_frame = tk.Frame(self.login_frame, bg=self.BG)
        link_frame.pack(pady=(2, 12))
        tk.Label(link_frame, text=self.t("friendly_links") + ": ", font=(SYSTEM_FONT, 9),
                 bg=self.BG, fg=self.BLUE_DARK).pack(side="left")

        self.flash_label_1 = tk.Label(link_frame,
                                      text="交大主页 " + self.t("click_me"),
                                      font=(SYSTEM_FONT, 9, "bold", "underline"),
                                      fg=self.RED_CLICK, bg=self.YELLOW_FLASH,
                                      cursor="hand2", padx=6, pady=2)
        self.flash_label_1.pack(side="left", padx=(0, 10))
        self.flash_label_1.bind("<Button-1>", lambda e: webbrowser.open(SCHOOL_URL))

        self.flash_label_2 = tk.Label(link_frame,
                                      text="后勤集团 " + self.t("click_me"),
                                      font=(SYSTEM_FONT, 9, "bold", "underline"),
                                      fg=self.RED_CLICK, bg=self.YELLOW_FLASH,
                                      cursor="hand2", padx=6, pady=2)
        self.flash_label_2.pack(side="left")
        self.flash_label_2.bind("<Button-1>", lambda e: webbrowser.open(HQ_URL))

    @staticmethod
    def _style_entry(entry):
        entry.config(relief="solid", bd=1, highlightthickness=0,
                     highlightbackground="#dcdfe6", highlightcolor="#2260d6")

    @staticmethod
    def _bind_hover(btn, normal_color, hover_color):
        def on_enter(e):
            btn.config(bg=hover_color)
        def on_leave(e):
            btn.config(bg=normal_color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    @staticmethod
    def _make_btn(parent, text, font, bg, fg, active_bg, active_fg, command,
                  width=None, relief="flat", bd=0, cursor="hand2", pack_side=None,
                  pack_padx=0, pack_pady=0, padx=0, pady=0):
        """跨平台兼容按钮：使用 Label + Frame 实现，bg/fg 在 Win/Mac/Linux 均生效。
        返回 Frame，可通过 frame._lbl 访问内部 Label 更新文字或样式。"""
        frame = tk.Frame(parent, bg=bg, cursor=cursor, relief=relief, bd=bd,
                         highlightbackground=bg, highlightthickness=0)
        lbl = tk.Label(frame, text=text, font=font, bg=bg, fg=fg)
        if width:
            lbl.config(width=width)
        lbl.pack(padx=padx, pady=pady)
        frame._lbl = lbl  # 暴露Label引用，供外部更新文本

        def _on_enter(e):
            frame.config(bg=active_bg, highlightbackground=active_bg)
            lbl.config(bg=active_bg, fg=active_fg)
        def _on_leave(e):
            frame.config(bg=bg, highlightbackground=bg)
            lbl.config(bg=bg, fg=fg)
        for w in (frame, lbl):
            w.bind("<Enter>", _on_enter)
            w.bind("<Leave>", _on_leave)
            w.bind("<Button-1>", lambda e: command())

        if pack_side:
            frame.pack(side=pack_side, padx=pack_padx, pady=pack_pady)
        return frame

    def _build_config_frame(self):
        self.config_frame = tk.Frame(self.root, bg=self.BG)

        canvas = tk.Canvas(self.config_frame, bg=self.BG, highlightthickness=0)
        v_scroll = tk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        h_scroll = tk.Scrollbar(self.config_frame, orient="horizontal", command=canvas.xview)
        self.config_scrollable = tk.Frame(canvas, bg=self.BG)

        self.config_scrollable.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._config_canvas = canvas
        self._canvas_win = canvas.create_window((0, 0), window=self.config_scrollable, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.coords(self._canvas_win,
            max(0, (e.width - self.config_scrollable.winfo_reqwidth()) // 2), 0) if hasattr(self, '_canvas_win') else None)
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * int(e.delta / 120), "units"))
        # 绑定 Shift+滚轮 水平滚动
        canvas.bind_all("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(-1 * int(e.delta / 120), "units"))

        # 用户信息栏
        ib = tk.Frame(self.config_scrollable, bg=self.BLUE_LIGHT, relief="solid", bd=1)
        ib.pack(fill="x", padx=10, pady=5)
        self.info_user_label = tk.Label(ib, text=self.t("current_user_none"),
                                        font=(SYSTEM_FONT, 10), bg=self.BLUE_LIGHT, fg=self.BLUE)
        self.info_user_label.pack(side="left", padx=10, pady=4)
        # 用户管理按钮（仅管理员可见，初始隐藏）
        self.btn_usermgr = self._make_btn(ib, "用户管理",
                                          font=(SYSTEM_FONT, 9),
                                          bg="#CC0000", fg="#FFD700",
                                          active_bg="#990000", active_fg="#FFD700",
                                          command=self._open_user_file,
                                          width=7, padx=5, pady=1)

        self.btn_logout = self._make_btn(ib, self.t("logout_btn"),
                                          font=(SYSTEM_FONT, 9),
                                          bg=self.BLUE, fg=self.WHITE,
                                          active_bg=self.BLUE_HOVER, active_fg=self.WHITE,
                                          command=self._back_to_login,
                                          width=6, padx=5, pady=1,
                                          pack_side="right", pack_padx=5, pack_pady=2)

        # 仿真参数
        self.lf_params = tk.LabelFrame(self.config_scrollable, text=self.t("sim_params"),
                                       font=(SYSTEM_FONT, 12, "bold"), bg=self.BG,
                                       fg=self.BLUE_DARK, padx=10, pady=10)
        self.lf_params.pack(fill="x", padx=10, pady=8)

        params = [
            ("ticks_label", "entry_ticks", "600", "ticks"),
            ("students_label", "entry_students", "30", "students"),
            ("spawn_label", "entry_spawn", "0.08", "spawn"),
        ]
        self._config_param_labels = []
        for i, (tkey, attr, default, tip_key) in enumerate(params):
            lbl = tk.Label(self.lf_params, text=self.t(tkey), font=(SYSTEM_FONT, 11), bg=self.BG)
            lbl.grid(row=i, column=0, padx=(5, 0), pady=6, sticky="e")
            self._config_param_labels.append((lbl, tkey))
            # ? 信息图标
            tip_icon = tk.Label(self.lf_params, text="?", font=(SYSTEM_FONT, 9, "bold"),
                                bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow",
                                width=2, relief="flat")
            tip_icon.grid(row=i, column=1, padx=(0, 3), pady=6, sticky="w")
            # 用 lambda 延迟获取，语言切换时自动更新
            _tk = tip_key
            ToolTip(tip_icon, lambda k=_tk: _get_tooltip(k, self.lang))
            entry = tk.Entry(self.lf_params, font=(SYSTEM_FONT, 11), width=12, relief="solid", bd=1)
            entry.insert(0, default)
            entry.grid(row=i, column=2, padx=(0, 5), pady=6, sticky="w")
            setattr(self, attr, entry)

        # 仿真开始时间
        i = len(params)
        lbl = tk.Label(self.lf_params, text=self.t("start_time_label"), font=(SYSTEM_FONT, 11), bg=self.BG)
        lbl.grid(row=i, column=0, padx=(5, 0), pady=6, sticky="e")
        self._config_param_labels.append((lbl, "start_time_label"))
        tip_st = tk.Label(self.lf_params, text="?", font=(SYSTEM_FONT, 9, "bold"),
                          bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2, relief="flat")
        tip_st.grid(row=i, column=1, padx=(0, 3), pady=6, sticky="w")
        ToolTip(tip_st, lambda: _get_tooltip("start_time", self.lang))
        self.entry_start_time = tk.Entry(self.lf_params, font=(SYSTEM_FONT, 11), width=12, relief="solid", bd=1)
        self.entry_start_time.insert(0, "07:00")
        self.entry_start_time.grid(row=i, column=2, padx=(0, 5), pady=6, sticky="w")

        # 食堂勾选（仿真参数内）
        i += 1
        canteen_lbl = tk.Label(self.lf_params, text=self.t("open_canteens_label"), font=(SYSTEM_FONT, 11), bg=self.BG)
        canteen_lbl.grid(row=i, column=0, padx=(5, 0), pady=6, sticky="e")
        self._config_param_labels.append((canteen_lbl, "open_canteens_label"))
        self._canteen_vars = {}
        cf = tk.Frame(self.lf_params, bg=self.BG)
        cf.grid(row=i, column=1, columnspan=2, padx=5, pady=6, sticky="w")
        for idx, name in enumerate(["四食堂", "一食堂", "留园", "学活食堂"]):
            var = tk.BooleanVar(value=(idx < 2))
            self._canteen_vars[name] = var
            tk.Checkbutton(cf, text=name, variable=var, font=(SYSTEM_FONT, 10),
                          bg=self.BG, activebackground=self.BG).pack(side="left", padx=4)

        # 策略选择
        self.lf_strategy = tk.LabelFrame(self.config_scrollable, text=self.t("strategy_label"),
                                         font=(SYSTEM_FONT, 12, "bold"), bg=self.BG,
                                         fg=self.BLUE_DARK, padx=10, pady=10)
        self.lf_strategy.pack(fill="x", padx=10, pady=8)
        self.lbl_choose_strat = tk.Label(self.lf_strategy, text=self.t("choose_strategy"),
                                         font=(SYSTEM_FONT, 11), bg=self.BG)
        self.lbl_choose_strat.grid(row=0, column=0, padx=(5, 0), pady=6, sticky="e")
        tip_strat = tk.Label(self.lf_strategy, text="?", font=(SYSTEM_FONT, 9, "bold"),
                             bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2)
        tip_strat.grid(row=0, column=1, padx=(0, 3), pady=6, sticky="w")
        ToolTip(tip_strat, lambda: _get_tooltip("strategy", self.lang))
        self.strategy_var = tk.StringVar(value="balanced")
        self.strategy_var.trace_add("write", self._on_strategy_change)
        ttk.Combobox(self.lf_strategy, textvariable=self.strategy_var,
                     values=["distance", "queue", "balanced"],
                     state="readonly", font=(SYSTEM_FONT, 11), width=14).grid(
            row=0, column=2, padx=(0, 5), pady=6, sticky="w")

        # 权重调节
        # 错峰开关
        self.stagger_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.lf_strategy, text=self.t("stagger_toggle"),
                       variable=self.stagger_var, font=(SYSTEM_FONT, 10),
                       bg=self.BG, activebackground=self.BG
                       ).grid(row=1, column=0, columnspan=3, padx=5, pady=4, sticky="w")

        self.lf_weight = tk.LabelFrame(self.config_scrollable, text=self.t("weight_label"),
                                       font=(SYSTEM_FONT, 12, "bold"), bg=self.BG,
                                       fg=self.BLUE_DARK, padx=10, pady=10)
        self.lf_weight.pack(fill="x", padx=10, pady=8)

        self.lbl_alpha = tk.Label(self.lf_weight, text=self.t("alpha_label"),
                                  font=(SYSTEM_FONT, 11), bg=self.BG)
        self.lbl_alpha.grid(row=0, column=0, padx=(5, 0), pady=6, sticky="e")
        tip_a = tk.Label(self.lf_weight, text="?", font=(SYSTEM_FONT, 9, "bold"),
                         bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2)
        tip_a.grid(row=0, column=1, padx=(0, 3), pady=6, sticky="w")
        ToolTip(tip_a, lambda: _get_tooltip("alpha", self.lang))
        self.alpha_var = tk.DoubleVar(value=0.5)
        alpha_slider = tk.Scale(self.lf_weight, from_=0.0, to=1.0, resolution=0.1,
                                variable=self.alpha_var, orient="horizontal", length=160,
                                bg=self.BG, font=(SYSTEM_FONT, 9))
        alpha_slider.grid(row=0, column=2, padx=5, pady=6, sticky="w")
        self.alpha_label = tk.Label(self.lf_weight, text="0.5", font=(SYSTEM_FONT, 11), bg=self.BG, width=5)
        self.alpha_label.grid(row=0, column=3, padx=5, pady=6)
        alpha_slider.config(command=lambda v: self.alpha_label.config(text=f"{float(v):.1f}"))

        self.lbl_beta = tk.Label(self.lf_weight, text=self.t("beta_label"),
                                 font=(SYSTEM_FONT, 11), bg=self.BG)
        self.lbl_beta.grid(row=1, column=0, padx=(5, 0), pady=6, sticky="e")
        tip_b = tk.Label(self.lf_weight, text="?", font=(SYSTEM_FONT, 9, "bold"),
                         bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2)
        tip_b.grid(row=1, column=1, padx=(0, 3), pady=6, sticky="w")
        ToolTip(tip_b, lambda: _get_tooltip("beta", self.lang))
        self.beta_var = tk.DoubleVar(value=0.5)
        beta_slider = tk.Scale(self.lf_weight, from_=0.0, to=1.0, resolution=0.1,
                               variable=self.beta_var, orient="horizontal", length=160,
                               bg=self.BG, font=(SYSTEM_FONT, 9))
        beta_slider.grid(row=1, column=2, padx=5, pady=6, sticky="w")
        self.beta_label = tk.Label(self.lf_weight, text="0.5", font=(SYSTEM_FONT, 11), bg=self.BG, width=5)
        self.beta_label.grid(row=1, column=3, padx=5, pady=6)
        beta_slider.config(command=lambda v: self.beta_label.config(text=f"{float(v):.1f}"))

        # 其他选项
        self.lf_other = tk.LabelFrame(self.config_scrollable, text=self.t("other_label"),
                                      font=(SYSTEM_FONT, 12, "bold"), bg=self.BG,
                                      fg=self.BLUE_DARK, padx=10, pady=10)
        self.lf_other.pack(fill="x", padx=10, pady=8)


        self.enable_viz_var = tk.BooleanVar(value=False)
        self.cb_viz = tk.Checkbutton(self.lf_other, text=self.t("enable_viz"),
                                     variable=self.enable_viz_var, font=(SYSTEM_FONT, 11),
                                     bg=self.BG)
        self.cb_viz.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tip_viz = tk.Label(self.lf_other, text="?", font=(SYSTEM_FONT, 9, "bold"),
                           bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2)
        tip_viz.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(tip_viz, lambda: _get_tooltip("viz", self.lang))

        self.config_path_var = tk.StringVar()
        self.btn_browse = self._make_btn(self.lf_other, self.t("browse_config"),
                                          font=(SYSTEM_FONT, 10),
                                          bg=self.BLUE_LIGHT, fg=self.BLUE,
                                          active_bg="#d0e0f8", active_fg=self.BLUE,
                                          command=self._load_config_file,
                                          padx=8, pady=2)
        self.btn_browse.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.lbl_config_path = tk.Label(self.lf_other, textvariable=self.config_path_var,
                                        font=(SYSTEM_FONT, 9), bg=self.BG, fg=self.BLUE)
        self.lbl_config_path.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 错峰对比按钮
        self.btn_peak = self._make_btn(self.lf_other, self.t("peak_shift_btn"),
                                        font=(SYSTEM_FONT, 10, "bold"),
                                        bg="#E67E22", fg=self.WHITE,
                                        active_bg="#D35400", active_fg=self.WHITE,
                                        command=self._run_peak_shift,
                                        padx=10, pady=3)
        self.btn_peak.grid(row=2, column=0, padx=5, pady=8, sticky="w")

        self.stop_peak_btn = self._make_btn(self.lf_other, "⏹",
                                             font=(SYSTEM_FONT, 10, "bold"),
                                             bg="#CC0000", fg=self.WHITE,
                                             active_bg="#990000", active_fg=self.WHITE,
                                             command=self._force_stop_simulation,
                                             padx=6, pady=3)
        self.stop_peak_btn.grid(row=2, column=1, padx=(2, 5), pady=8, sticky="w")
        tip_peak = tk.Label(self.lf_other, text="?", font=(SYSTEM_FONT, 9, "bold"),
                            bg="#d0d8e8", fg=self.BLUE, cursor="question_arrow", width=2)
        tip_peak.grid(row=2, column=2, padx=(0, 5), pady=8, sticky="w")
        ToolTip(tip_peak, lambda: _get_tooltip("peak", self.lang))

        # 启动按钮
        lf = tk.Frame(self.config_scrollable, bg=self.BG)
        lf.pack(fill="x", padx=10, pady=10)
        self.launch_btn = self._make_btn(lf, self.t("launch_btn"),
                                          font=(SYSTEM_FONT, 14, "bold"),
                                          bg=self.BLUE, fg=self.WHITE,
                                          active_bg=self.BLUE_HOVER, active_fg=self.WHITE,
                                          command=self._launch_simulation,
                                          width=16, padx=14, pady=6)
        self.launch_btn.pack(side="left", padx=2, pady=2)

        self.stop_btn = self._make_btn(lf, self.t("stop_btn"),
                                        font=(SYSTEM_FONT, 14, "bold"),
                                        bg="#CC0000", fg=self.WHITE,
                                        active_bg="#990000", active_fg=self.WHITE,
                                        command=self._force_stop_simulation,
                                        width=14, padx=14, pady=6)
        # 停止按钮初始隐藏，仿真启动后才显示

        # 结果显示
        self.lf_result = tk.LabelFrame(self.config_scrollable, text=self.t("result_label"),
                                       font=(SYSTEM_FONT, 12, "bold"), bg=self.BG,
                                       fg=self.BLUE_DARK, padx=10, pady=10)
        self.lf_result.pack(fill="both", expand=True, padx=10, pady=8)
        self.result_text = tk.Text(self.lf_result, font=(SYSTEM_FONT, 10), wrap="word",
                                   relief="solid", bd=1, height=12)
        self.result_text.pack(fill="both", expand=True)

        # 导出按钮（仿真完成后出现）
        self.export_frame = tk.Frame(self.lf_result, bg=self.BG)
        self.btn_export = self._make_btn(self.export_frame, "导出报告",
                                          font=(SYSTEM_FONT, 10, "bold"),
                                          bg="#27AE60", fg=self.WHITE,
                                          active_bg="#1E8449", active_fg=self.WHITE,
                                          command=self._show_export_dialog,
                                          padx=12, pady=4,
                                          pack_side="left", pack_padx=5)

    # ====================== 语言切换 ======================
    def _set_lang_btn_style(self, code, bg_color):
        frame, lbl = self._lang_btns[code]
        frame.config(bg=bg_color, highlightbackground=bg_color)
        lbl.config(bg=bg_color)

    def _switch_lang(self, code):
        if code == self.lang:
            return
        self.lang = code
        for c in self._lang_btns:
            self._set_lang_btn_style(c, self.BLUE_HOVER if c == code else self.BLUE_DARK)
        self._apply_language()

    def _apply_language(self):
        self.root.title(self.t("window_title"))
        self.lbl_sys_name.config(text=self.t("system_name"))
        self.lbl_subtitle.config(text=self.t("subtitle"))

        for c in self._lang_btns:
            self._set_lang_btn_style(c, self.BLUE_HOVER if c == self.lang else self.BLUE_DARK)

        self.lbl_card_title.config(text=self.t("user_login"))
        self.lbl_role.config(text=self.t("role_label"))
        for i, val_key in enumerate(["student", "teacher"]):
            self._role_buttons[i].config(text=self.t(val_key))
        self.lbl_account.config(text=self.t("account_label"))
        self.lbl_password.config(text=self.t("password_label"))
        self.lbl_captcha.config(text=self.t("captcha_label"))
        self.btn_local._lbl.config(text=self.t("login_btn"))
        self.btn_register.config(text=self.t("register_btn"))
        self.lbl_forget.config(text=self.t("forgot_pwd"))
        self.btn_guest.config(text=self.t("guest_btn"))
        self.lbl_pwd_hint.config(text=self.t("default_pwd_hint"))
        self.lbl_first_login.config(text=self.t("first_login_hint"))

        self.flash_label_1.config(text="交大主页 " + self.t("click_me"))
        self.flash_label_2.config(text="后勤集团 " + self.t("click_me"))

        if self.current_user:
            self.info_user_label.config(text=self.t("current_user").format(
                info=f"{self.t(self.current_role)} | {self.current_user}"))
            self.status_bar.config(text=self.t("status_logged_in").format(
                role=self.t(self.current_role), user=self.current_user))
        else:
            self.info_user_label.config(text=self.t("current_user_none"))
            self.status_bar.config(text=self.t("not_logged_in"))

        self.btn_logout._lbl.config(text=self.t("logout_btn"))
        self.lf_params.config(text=self.t("sim_params"))
        for lbl, tkey in self._config_param_labels:
            lbl.config(text=self.t(tkey))
        self.lf_strategy.config(text=self.t("strategy_label"))
        self.lbl_choose_strat.config(text=self.t("choose_strategy"))
        # 刷新错峰开关
        for w in self.lf_strategy.winfo_children():
            if isinstance(w, tk.Checkbutton):
                w.config(text=self.t("stagger_toggle"))
        self.lf_weight.config(text=self.t("weight_label"))
        self.lbl_alpha.config(text=self.t("alpha_label"))
        self.lbl_beta.config(text=self.t("beta_label"))
        self.lf_other.config(text=self.t("other_label"))
        self.cb_viz.config(text=self.t("enable_viz"))
        self.btn_browse._lbl.config(text=self.t("browse_config"))
        self.launch_btn._lbl.config(text=self.t("launch_btn"))
        self.stop_btn._lbl.config(text=self.t("stop_btn"))
        self.btn_peak._lbl.config(text=self.t("peak_shift_btn"))
        self.lf_result.config(text=self.t("result_label"))

    # ====================== 闪烁动画 ======================
    def _start_flash(self):
        if self._flash_job is not None:
            return
        yellow_on = True

        def _toggle():
            nonlocal yellow_on
            yellow_on = not yellow_on
            bg = self.YELLOW_FLASH if yellow_on else "#ffeb80"
            try:
                if self.flash_label_1.winfo_exists():
                    self.flash_label_1.config(bg=bg)
                if self.flash_label_2.winfo_exists():
                    self.flash_label_2.config(bg=bg)
                self._flash_job = self.root.after(600, _toggle)
            except tk.TclError:
                pass

        self._flash_job = self.root.after(600, _toggle)

    # ====================== 验证码 ======================
    def _generate_captcha(self):
        self.captcha_code = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        self.captcha_canvas.delete("all")
        bg_color = random.choice(["#e2e6ea", "#dce0e5", "#dde3e8"])
        self.captcha_canvas.config(bg=bg_color)
        for _ in range(8):
            x1, y1 = random.randint(0, 110), random.randint(0, 35)
            x2, y2 = random.randint(0, 110), random.randint(0, 35)
            self.captcha_canvas.create_line(x1, y1, x2, y2,
                                            fill=random.choice(["#888888", "#999999"]), width=1)
        for _ in range(40):
            x, y = random.randint(0, 110), random.randint(0, 35)
            self.captcha_canvas.create_oval(x, y, x + 1, y + 1,
                                            fill=random.choice(["#666666", "#777777"]))
        for idx, char in enumerate(self.captcha_code):
            x = 15 + idx * 22 + random.randint(-4, 4)
            y = 20 + random.randint(-5, 5)
            color = random.choice(["#333333", "#444444", "#555555"])
            self.captcha_canvas.create_text(x, y, text=char, fill=color,
                                            font=("黑体", 17, "bold"))

    # ====================== 管理员登录 ======================
    def _admin_login(self):
        """弹出管理员选择+密钥验证窗口"""

        # ---- 通用 GIF 加载器 ----
        def _load_gif_frames(gif_bytes_or_path, resize_to, from_bytes=False):
            frames, durations = [], []
            try:
                from PIL import Image as PILImage, ImageTk as PILImageTk
                import io
                if from_bytes:
                    gif_img = PILImage.open(io.BytesIO(gif_bytes_or_path))
                else:
                    gif_img = PILImage.open(gif_bytes_or_path)
                while True:
                    dur = gif_img.info.get('duration', 30)
                    durations.append(dur)
                    frame = PILImageTk.PhotoImage(gif_img.copy().resize(resize_to, PILImage.LANCZOS))
                    frames.append(frame)
                    gif_img.seek(len(frames))
            except (EOFError, Exception):
                pass
            return frames, durations

        # 标题栏 GIF（抽象小猫）
        TITLE_FRAMES, TITLE_DURS = [], []
        try:
            from assets._cat_gif import get_gif_bytes
            TITLE_FRAMES, TITLE_DURS = _load_gif_frames(get_gif_bytes(), (42, 42), from_bytes=True)
        except Exception:
            pass
        if not TITLE_FRAMES:
            p = os.path.join(os.path.dirname(__file__), "抽象小猫.gif")
            if HAS_PIL and os.path.exists(p):
                TITLE_FRAMES, TITLE_DURS = _load_gif_frames(p, (42, 42))

        # 正文区域 GIF（功夫耄耋）
        BODY_FRAMES, BODY_DURS = [], []
        try:
            from assets._gif2_data import get_gif2_bytes
            BODY_FRAMES, BODY_DURS = _load_gif_frames(get_gif2_bytes(), (90, 152), from_bytes=True)
        except Exception:
            pass
        if not BODY_FRAMES:
            p = os.path.join(os.path.dirname(__file__), "功夫耄耋.gif")
            if HAS_PIL and os.path.exists(p):
                BODY_FRAMES, BODY_DURS = _load_gif_frames(p, (90, 152))

        # 底部爱心 GIF（heart3d）
        HEART_FRAMES, HEART_DURS = [], []
        try:
            from assets._heart_data import get_heart_bytes
            HEART_FRAMES, HEART_DURS = _load_gif_frames(get_heart_bytes(), (28, 24), from_bytes=True)
        except Exception:
            pass
        if not HEART_FRAMES:
            p = os.path.join(os.path.dirname(__file__), "heart3d.gif")
            if HAS_PIL and os.path.exists(p):
                HEART_FRAMES, HEART_DURS = _load_gif_frames(p, (28, 24))

        # ---- 创建弹窗 ----
        W, H = 520, 355
        dlg = tk.Toplevel(self.root)
        dlg.title("管理员验证")
        dlg.geometry(f"{W}x{H}")
        dlg.resizable(False, False)
        dlg.config(bg="#FFF8DC")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.root.winfo_x() + (600 - W) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - H) // 2
        dlg.geometry(f"+{x}+{y}")

        # ---- 通用动画 Label 工厂 ----
        def _make_anim_label(parent, frames, durations, bgcolor):
            lbl = tk.Label(parent, bg=bgcolor)
            if frames:
                lbl._frames = frames
                lbl._durs = durations
                lbl._idx = 0
                lbl.config(image=frames[0])
                def _anim(lbl=lbl):
                    if not dlg.winfo_exists():
                        return
                    lbl._idx = (lbl._idx + 1) % len(lbl._frames)
                    lbl.config(image=lbl._frames[lbl._idx])
                    lbl._timer = dlg.after(lbl._durs[lbl._idx], lambda: _anim(lbl))
                lbl._timer = dlg.after(durations[0], lambda: _anim(lbl))
            return lbl

        # ========== 标题栏 ==========
        title_bar = tk.Frame(dlg, bg="#CC0000")
        title_bar.pack(fill="x")

        _make_anim_label(title_bar, TITLE_FRAMES, TITLE_DURS, "#CC0000").pack(
            side="left", padx=(10, 0), pady=4)
        tk.Label(title_bar, text="管理员登录", font=(SYSTEM_FONT, 15, "bold"),
                 bg="#CC0000", fg="#FFD700", pady=8).pack(side="left", expand=True)
        _make_anim_label(title_bar, TITLE_FRAMES, TITLE_DURS, "#CC0000").pack(
            side="right", padx=(0, 10), pady=4)

        # ========== 正文区域 ==========
        body = tk.Frame(dlg, bg="#FFF8DC")
        body.pack(fill="both", expand=True)

        # 左侧功夫耄耋 GIF
        _make_anim_label(body, BODY_FRAMES, BODY_DURS, "#FFF8DC").pack(
            side="left", padx=(20, 10), pady=(6, 6))

        # 右侧功夫耄耋 GIF
        _make_anim_label(body, BODY_FRAMES, BODY_DURS, "#FFF8DC").pack(
            side="right", padx=(10, 20), pady=(6, 6))

        # 中央表单
        center = tk.Frame(body, bg="#FFF8DC")
        center.pack(expand=True)

        sf = tk.Frame(center, bg="#FFF8DC")
        sf.pack(pady=(2, 6))
        tk.Label(sf, text="选择管理员：", font=(SYSTEM_FONT, 11), bg="#FFF8DC").pack(
            side="left", padx=(0, 6))
        admin_names = [f"{v['name']} ({v['role']})" for v in _ADMINS.values()]
        admin_ids = list(_ADMINS.keys())
        admin_var = tk.StringVar(value=admin_names[0])
        combo = ttk.Combobox(sf, textvariable=admin_var, values=admin_names,
                             state="readonly", font=(SYSTEM_FONT, 11), width=16)
        combo.pack(side="left")

        kf = tk.Frame(center, bg="#FFF8DC")
        kf.pack(pady=(0, 6))
        tk.Label(kf, text="密  钥：", font=(SYSTEM_FONT, 11), bg="#FFF8DC").pack(
            side="left", padx=(0, 6))
        key_entry = tk.Entry(kf, font=(SYSTEM_FONT, 11), width=16, show="*",
                             relief="solid", bd=1)
        key_entry.pack(side="left")
        key_entry.bind("<Return>", lambda e: _verify())
        key_entry.focus_set()

        tk.Label(center, text="仅限管理员使用，密钥请妥善保管",
                 font=(SYSTEM_FONT, 8), fg="#999999", bg="#FFF8DC").pack()

        def _verify():
            idx = combo.current()
            if idx < 0:
                return
            uid = admin_ids[idx]
            admin_info = _ADMINS[uid]
            if key_entry.get().strip() == admin_info["key"]:
                self.current_user = f"{admin_info['name']}({admin_info['role']})"
                self.current_role = "admin"
                dlg.destroy()
                messagebox.showinfo(self.t("login_success"),
                                    self.t("welcome", role="管理员", account=admin_info['name']))
                self._show_config_panel()
            else:
                messagebox.showerror(self.t("error"), self.t("admin_key_error"), parent=dlg)
                key_entry.delete(0, tk.END)

        btn_frame = tk.Frame(center, bg="#FFF8DC")
        btn_frame.pack(pady=(4, 0))
        self._make_btn(btn_frame, "验证登录",
                       font=(SYSTEM_FONT, 11, "bold"),
                       bg="#CC0000", fg="#FFD700",
                       active_bg="#990000", active_fg="#FFD700",
                       command=_verify, padx=20, pady=5,
                       pack_side="left", pack_padx=6)
        self._make_btn(btn_frame, "取消",
                       font=(SYSTEM_FONT, 10),
                       bg="#DDDDDD", fg="#333333",
                       active_bg="#BBBBBB", active_fg="#333333",
                       command=dlg.destroy, padx=14, pady=4,
                       pack_side="left", pack_padx=6)

        # ========== 底部爱心排 ==========
        bottom_bar = tk.Frame(dlg, bg="#FFF8DC")
        bottom_bar.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(bottom_bar, bg="#FFF8DC")
        inner.pack(expand=True)
        for _ in range(11):
            lbl = tk.Label(inner, bg="#FFF8DC")
            if HEART_FRAMES:
                lbl._frames = HEART_FRAMES
                lbl._durs = HEART_DURS
                lbl._idx = 0
                lbl.config(image=HEART_FRAMES[0])
                def _anim_heart(lbl=lbl):
                    if not dlg.winfo_exists():
                        return
                    lbl._idx = (lbl._idx + 1) % len(lbl._frames)
                    lbl.config(image=lbl._frames[lbl._idx])
                    lbl._timer = dlg.after(lbl._durs[lbl._idx], lambda l=lbl, f=_anim_heart: f(l))
                lbl._timer = dlg.after(HEART_DURS[0], lambda l=lbl, f=_anim_heart: f(l))
            lbl.pack(side="left", padx=8)

    # ====================== 登录逻辑 ======================
    def _on_strategy_change(self, *args):
        """选策略时自动调整权重滑块"""
        s = self.strategy_var.get()
        preset = {"distance": (0.9, 0.1), "queue": (0.1, 0.9), "balanced": (0.5, 0.5)}
        if s in preset:
            a, b = preset[s]
            self.alpha_var.set(a); self.beta_var.set(b)
            self.alpha_label.config(text=f"{a:.1f}")
            self.beta_label.config(text=f"{b:.1f}")

    def _on_role_change(self, *args):
        pass

    def _clear_login(self):
        self.entry_account.delete(0, tk.END)
        self.entry_password.delete(0, tk.END)
        self.entry_captcha.delete(0, tk.END)
        self._generate_captcha()

    def _local_login(self):
        # 管理员弹窗 grab 激活时忽略回车，防止弹出"请选择身份"
        if self.root.grab_current() is not None:
            return
        # 已登录状态下按回车直接忽略
        if self.current_user is not None:
            return
        role = self.role_var.get()
        account = self.entry_account.get().strip()
        password = self.entry_password.get()
        input_captcha = self.entry_captcha.get().strip()

        if not role:
            messagebox.showwarning(self.t("prompt"), self.t("select_role_first"))
            return
        if not account:
            messagebox.showwarning(self.t("input_error"), self.t("account_empty"))
            return
        if not password:
            messagebox.showwarning(self.t("input_error"), self.t("password_empty"))
            return

        if not input_captcha:
            messagebox.showwarning(self.t("input_error"), self.t("captcha_empty"))
            return

        if input_captcha.upper() != self.captcha_code.upper():
            messagebox.showerror(self.t("error"), self.t("captcha_error"))
            self.entry_captcha.delete(0, tk.END)
            self._generate_captcha()
            return

        valid, result = validate_account(account, role)
        if not valid:
            messagebox.showwarning(self.t("input_error"), result)
            return

        valid, result = validate_password(password)
        if not valid:
            messagebox.showwarning(self.t("input_error"), result)
            return

        key = f"{role}:{account}"
        if key in self.login_attempts and self.login_attempts[key] <= 0:
            messagebox.showerror(self.t("error"), self.t("account_locked"))
            return

        users = load_users()
        stored_pwd = users.get(key)
        if stored_pwd is None:
            messagebox.showerror(self.t("login_failed"),
                                 self.t("account_not_registered"))
            self.entry_captcha.delete(0, tk.END)
            self._generate_captcha()
            return

        if password == stored_pwd:
            self._on_login_success(role, account, key)
        else:
            self.login_attempts[key] = self.login_attempts.get(key, MAX_ATTEMPTS) - 1
            remaining = self.login_attempts[key]
            msg = self.t("pw_error_msg", remaining=remaining)
            if remaining <= 0:
                msg += self.t("pw_locked_msg")
            messagebox.showerror(self.t("login_failed"), msg)
            self.entry_captcha.delete(0, tk.END)
            self._generate_captcha()

    def _on_login_success(self, role, account, key):
        self.current_user = account
        self.current_role = role
        self.login_attempts.pop(key, None)
        self.entry_captcha.delete(0, tk.END)
        role_display = self.t(role)
        messagebox.showinfo(self.t("login_success"),
                            self.t("welcome", role=role_display, account=account))
        self._show_config_panel()

    def _forgot_password(self):
        messagebox.showinfo(self.t("forgot_title"),
                            self.t("forgot_msg", email=ADMIN_EMAIL))

    def _guest_login(self):
        """访客模式：直接跳转交大主页"""
        webbrowser.open(SCHOOL_URL)

    def _register(self):
        """注册新账号"""
        role = self.role_var.get()
        if not role:
            messagebox.showwarning(self.t("prompt"), self.t("select_role_first"))
            return

        role_display = self.t(role)
        uid = simpledialog.askstring(self.t("register_title"),
                                     self.t("register_prompt", role=role_display),
                                     parent=self.root)
        if not uid:
            return

        uid = uid.strip()
        valid, msg = validate_account(uid, role)
        if not valid:
            messagebox.showerror(self.t("register_failed"), msg)
            return

        users = load_users()
        key = f"{role}:{uid}"
        if key in users:
            messagebox.showwarning(self.t("prompt"), self.t("register_exists"))
            return

        default_pwd = get_default_password(uid)
        save_user(role, uid, default_pwd)
        messagebox.showinfo(self.t("register_success"),
                            self.t("register_done", role=role_display, uid=uid, pwd=default_pwd))

    # ---------- 导出报告 ----------
    def _show_export_dialog(self):
        """弹出导出格式和路径选择窗口"""
        engine = getattr(self, '_last_engine', None)
        if engine is None:
            messagebox.showwarning(self.t("error"), self.t("not_login_msg"))
            return

        dlg = tk.Toplevel(self.root)
        dlg.title(self.t("export_title"))
        dlg.geometry("420x300")
        dlg.resizable(False, False)
        dlg.config(bg="#FFF8DC")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.root.winfo_x() + (600 - 380) // 2
        y = self.root.winfo_y() + (690 - 250) // 2
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text=self.t("export_title"), font=(SYSTEM_FONT, 14, "bold"),
                 bg="#27AE60", fg="white", pady=8).pack(fill="x")

        tk.Label(dlg, text=self.t("export_select_format"), font=(SYSTEM_FONT, 11),
                 bg="#FFF8DC").pack(pady=(10, 4))
        fmt_var = tk.StringVar(value="xlsx")
        fmts = [("Excel 表格 (.xlsx)", "xlsx"),
                ("Word 文档 (.docx)", "docx"),
                ("PDF 文档 (.pdf)", "pdf")]
        ff = tk.Frame(dlg, bg="#FFF8DC")
        ff.pack()
        for text, val in fmts:
            tk.Radiobutton(ff, text=text, variable=fmt_var, value=val,
                          font=(SYSTEM_FONT, 10), bg="#FFF8DC",
                          activebackground="#FFF8DC").pack(anchor="w", padx=20)

        tk.Label(dlg, text=self.t("export_save_path"), font=(SYSTEM_FONT, 11),
                 bg="#FFF8DC").pack(pady=(10, 4))
        pf = tk.Frame(dlg, bg="#FFF8DC")
        pf.pack()
        path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "仿真报告"))
        path_entry = tk.Entry(pf, textvariable=path_var, font=(SYSTEM_FONT, 10), width=30)
        path_entry.pack(side="left", padx=(10, 4))
        tk.Button(pf, text=self.t("export_browse"), font=(SYSTEM_FONT, 9),
                  command=lambda: self._browse_export_path(path_var, fmt_var.get())
                  ).pack(side="left")

        def _do_export():
            fmt = fmt_var.get()
            base = path_var.get().strip()
            if not base:
                messagebox.showwarning("路径为空", "请输入保存路径", parent=dlg)
                return
            for old_ext in [".xlsx", ".docx", ".pdf"]:
                if base.endswith(old_ext):
                    base = base[:-len(old_ext)]
                    break
            exts = {"xlsx": ".xlsx", "docx": ".docx", "pdf": ".pdf"}
            path = base + exts[fmt]
            try:
                from export_report import export_excel, export_docx, export_pdf
                th = engine.tick_history
                if fmt == "xlsx":
                    path = export_excel(engine, path, th)
                elif fmt == "docx":
                    path = export_docx(engine, path, th)
                else:
                    path = export_pdf(engine, path, th)
                dlg.destroy()
                if sys.platform == "darwin":
                    os.system(f'open -R "{path}"')
                elif sys.platform == "win32":
                    os.startfile(os.path.dirname(path))
                messagebox.showinfo(self.t("success"), f"{self.t('export_success')}:\n{path}")
            except ImportError as e:
                messagebox.showerror("缺少依赖", f"请先安装依赖:\n{e}", parent=dlg)
            except Exception as e:
                messagebox.showerror(self.t("error"), str(e), parent=dlg)

        bf = tk.Frame(dlg, bg="#FFF8DC")
        bf.pack(pady=(12, 8))
        self._make_btn(bf, self.t("export_btn"), font=(SYSTEM_FONT, 11, "bold"),
                       bg="#27AE60", fg="white", active_bg="#1E8449", active_fg="white",
                       command=_do_export, padx=16, pady=4,
                       pack_side="left", pack_padx=8)
        self._make_btn(bf, self.t("cancel"), font=(SYSTEM_FONT, 10),
                       bg="#DDD", fg="#333", active_bg="#BBB", active_fg="#333",
                       command=dlg.destroy, padx=12, pady=4,
                       pack_side="left", pack_padx=8)

    def _auto_save(self, engine, settings):
        """根据设置自动保存仿真结果"""
        try:
            from export_report import export_excel, export_docx, export_pdf
            th = engine.tick_history
            base = settings.get("path", os.path.join(os.path.expanduser("~"), "Desktop", "仿真报告"))
            saved = []
            for fmt in settings.get("formats", ["xlsx"]):
                for old_ext in [".xlsx", ".docx", ".pdf"]:
                    if base.endswith(old_ext):
                        base = base[:-len(old_ext)]
                        break
                exts = {"xlsx": ".xlsx", "docx": ".docx", "pdf": ".pdf"}
                path = base + exts[fmt]
                if fmt == "xlsx":
                    export_excel(engine, path, th)
                elif fmt == "docx":
                    export_docx(engine, path, th)
                else:
                    export_pdf(engine, path, th)
                saved.append(os.path.basename(path))
            if saved:
                self.result_text.insert(tk.END, f"\n[自动保存] {', '.join(saved)}\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"\n[自动保存失败] {e}\n")

    def _browse_export_path(self, path_var, fmt):
        """浏览保存路径，去掉系统自动加的后缀"""
        exts = {"xlsx": [("Excel 文件", "*.xlsx")],
                "docx": [("Word 文件", "*.docx")],
                "pdf": [("PDF 文件", "*.pdf")]}
        filepath = filedialog.asksaveasfilename(
            title="保存报告",
            filetypes=exts.get(fmt, [("All", "*.*")]),
            defaultextension=f".{fmt}",
            initialdir=os.path.expanduser("~/Desktop"),
            initialfile="仿真报告"
        )
        if filepath:
            # 去掉系统对话可能添加的任何已知后缀
            for ext in [".xlsx", ".docx", ".pdf"]:
                if filepath.endswith(ext):
                    filepath = filepath[:-len(ext)]
                    break
            path_var.set(filepath)

    # ---------- 错峰对比 ----------
    def _run_peak_shift(self):
        """在 GUI 中运行错峰对比分析并展示结果图（线程化，逐 gap 检查中断标志）"""
        try:
            students = int(self.entry_students.get())
        except ValueError:
            messagebox.showwarning(self.t("param_invalid"), self.t("students_must_int"))
            return

        self._peak_stop_requested = False
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "正在运行错峰对比分析...\n")
        self.btn_peak._lbl.config(text="⏳ 运行中…")
        self.stop_btn.pack(side="left", padx=2, pady=2)
        self.root.update()

        GAP_VALUES = [0, 5, 10, 15, 20, 30]

        def run_in_thread():
            try:
                from peak_shift import run_staggered_simulation, print_summary
                # 逐 gap 运行，每轮检查中断标志（解决大数据量下停止无响应）
                results = []
                for gap in GAP_VALUES:
                    if self._peak_stop_requested:
                        return
                    label = "同时下课" if gap == 0 else f"错峰 {gap} 分钟"
                    if len(GAP_VALUES) <= 1:
                        pass  # 不打印进度
                    result = run_staggered_simulation(gap, students, 300,
                                                        is_cancelled=lambda: self._peak_stop_requested)
                    results.append(result)
                    if result.get('cancelled'):
                        return  # 仿真内部被中断
                    self.root.after(0,
                        lambda l=label, r=result: self.result_text.insert(
                            tk.END, f"  {l}: 最大排队={r['max_queue']}, 平均等待={r['avg_wait']:.1f}\n"))

                if self._peak_stop_requested:
                    return
                print_summary(results)

                def _finish():
                    if self._peak_stop_requested:
                        self.stop_btn.pack_forget()
                        self.btn_peak._lbl.config(text=self.t("peak_shift_btn"))
                        return
                    self.stop_btn.pack_forget()
                    self.btn_peak._lbl.config(text=self.t("peak_shift_btn"))
                    try:
                        from peak_shift import plot_comparison
                        import os as _os
                        output_path = _os.path.join(_os.path.expanduser("~"), "Desktop", "peak_shift")
                        plot_comparison(results, output_path)
                    except Exception as pe:
                        self.result_text.insert(tk.END, f"\n图表生成失败: {pe}\n")
                    self.result_text.delete("1.0", tk.END)
                    self.result_text.insert(tk.END, "=" * 50 + "\n")
                    self.result_text.insert(tk.END, "  错峰下课方案对比 — 完成\n")
                    self.result_text.insert(tk.END, "=" * 50 + "\n\n")

                    baseline = results[0]['max_queue'] if results else 1
                    self.result_text.insert(tk.END,
                        f"{'方案':<14} {'最大排队':>8} {'平均等待':>8} {'排队峰降':>8}\n")
                    self.result_text.insert(tk.END, "-" * 42 + "\n")
                    for r in results:
                        label = "同时下课" if r['gap_minutes'] == 0 else f"错峰{r['gap_minutes']}分钟"
                        reduction = (baseline - r['max_queue']) / max(baseline, 1) * 100
                        red_str = f"↓{reduction:.0f}%" if r['gap_minutes'] > 0 else "-"
                        self.result_text.insert(tk.END,
                            f"{label:<14} {r['max_queue']:>8} {r['avg_wait']:>8.1f} {red_str:>8}\n")

                    img_path = os.path.join(os.path.expanduser("~"), "Desktop", "peak_shift_comparison.png")
                    if os.path.exists(img_path):
                        if sys.platform == "darwin":
                            os.system(f'open "{img_path}"')
                        elif sys.platform == "win32":
                            os.startfile(img_path)
                        else:
                            os.system(f'xdg-open "{img_path}"')
                        self.result_text.insert(tk.END, "\n对比图表已在外部窗口中打开\n")
                self.root.after(0, _finish)
            except Exception as e:
                self.root.after(0, lambda: (
                    self.stop_btn.pack_forget(),
                    self.btn_peak._lbl.config(text=self.t("peak_shift_btn")),
                    self.result_text.delete("1.0", tk.END),
                    self.result_text.insert(tk.END, f"错峰对比失败:\n{e}")
                ))
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    # ---------- 用户管理 ----------
    def _open_user_file(self):
        """管理员打开用户文件编辑"""
        if not os.path.exists(USER_FILE):
            open(USER_FILE, "w", encoding="utf-8").close()
        if sys.platform == "darwin":
            os.system(f'open "{USER_FILE}"')
        elif sys.platform == "win32":
            os.startfile(USER_FILE)
        else:
            os.system(f'xdg-open "{USER_FILE}"')

    # ---------- 面板切换 ----------
    def _show_config_panel(self):
        self.login_frame.pack_forget()
        self.config_frame.pack(fill="both", expand=True)
        if self.current_role == "admin":
            self.btn_usermgr.pack(side="right", padx=3, pady=2, before=self.btn_logout)
        role_display = self.t(self.current_role) if self.current_role != "admin" else self.t("admin")
        self.info_user_label.config(text=self.t("current_user").format(
            info=f"{role_display} | {self.current_user}"))
        self.status_bar.config(text=self.t("status_logged_in").format(
            role=role_display, user=self.current_user))
        # Canvas 内容延迟刷新（解决 Tk 窗口不渲染问题）
        def _refresh_canvas():
            self._config_canvas.yview_moveto(1)
            self._config_canvas.yview_moveto(0)
            self._config_canvas.update_idletasks()
        self.root.after(50, _refresh_canvas)

    def _back_to_login(self):
        self.current_user = None
        self.current_role = None
        self._config_data = None
        self._last_engine = None
        self._auto_save_settings = None
        self.btn_usermgr.pack_forget()
        self.export_frame.pack_forget()
        self.result_text.delete("1.0", tk.END)
        self.config_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.info_user_label.config(text=self.t("current_user_none"))
        self.status_bar.config(text=self.t("not_logged_in"))
        # 重置所有参数为默认值
        self.entry_ticks.delete(0, tk.END); self.entry_ticks.insert(0, "600")
        self.entry_students.delete(0, tk.END); self.entry_students.insert(0, "30")
        self.entry_spawn.delete(0, tk.END); self.entry_spawn.insert(0, "0.08")
        self.entry_start_time.delete(0, tk.END); self.entry_start_time.insert(0, "07:00")
        self.strategy_var.set("balanced")
        self.alpha_var.set(0.5); self.beta_var.set(0.5)
        self.alpha_label.config(text="0.5"); self.beta_label.config(text="0.5")
        self.enable_viz_var.set(False)
        self.config_path_var.set("")
        for idx, name in enumerate(["四食堂", "一食堂", "留园", "学活食堂"]):
            self._canteen_vars[name].set(idx < 2)
        self._clear_login()

    # ---------- 配置加载 ----------
    def _load_config_file(self):
        filepath = filedialog.askopenfilename(
            title=self.t("select_config"),
            filetypes=[(self.t("json_files"), "*.json"), (self.t("all_files"), "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            sp = data.get("simulation_params", {})
            ap = data.get("algorithm_params", {})

            for entry, key in [
                (self.entry_ticks, "max_ticks"),
                (self.entry_students, "student_count"),
                (self.entry_spawn, "spawn_rate"),
            ]:
                entry.delete(0, tk.END)
                entry.insert(0, str(sp.get(key, entry.get())))

            dw = ap.get("distance_weight", 0.3)
            qw = ap.get("queue_weight", 0.7)
            if dw >= 0.7:
                self.strategy_var.set("distance")
            elif qw >= 0.7:
                self.strategy_var.set("queue")
            else:
                self.strategy_var.set("balanced")

            self.alpha_var.set(dw)
            self.beta_var.set(qw)
            self.enable_viz_var.set(sp.get("enable_visualization", False))
            self.config_path_var.set(filepath)

            # 保存完整配置（含坐标），启动仿真时覆盖 campus_bounds.json
            self._config_data = data
            self._auto_save_settings = None

            messagebox.showinfo(self.t("load_success"),
                                self.t("config_loaded", file=os.path.basename(filepath)))
        except Exception as e:
            messagebox.showerror(self.t("load_failed"),
                                 self.t("config_parse_error", e=str(e)))

    # ---------- 参数校验 ----------
    def validate_params(self):
        errors = []
        try:
            ticks = int(self.entry_ticks.get())
            if ticks <= 0:
                errors.append(self.t("ticks_must_positive"))
        except ValueError:
            errors.append(self.t("ticks_must_int"))

        try:
            students = int(self.entry_students.get())
            if students < 0:
                errors.append(self.t("students_not_negative"))
        except ValueError:
            errors.append(self.t("students_must_int"))

        try:
            spawn_rate = float(self.entry_spawn.get())
            if not (0 <= spawn_rate <= 1):
                errors.append(self.t("spawn_range"))
        except ValueError:
            errors.append(self.t("spawn_must_number"))

        # 开始时间校验
        try:
            st = self.entry_start_time.get().strip()
            parts = st.split(":")
            if len(parts) != 2 or len(parts[1]) != 2 or len(parts[0]) < 1 or len(parts[0]) > 2:
                errors.append(self.t("start_time_invalid"))
            else:
                h, m = int(parts[0]), int(parts[1])
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    errors.append(self.t("start_time_range"))
        except ValueError:
            errors.append(self.t("start_time_invalid"))

        return errors

    # ---------- 强制停止仿真 ----------
    def _force_stop_simulation(self):
        """强制关闭 Matplotlib 可视化窗口 / 中断错峰对比"""
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except Exception:
            pass
        # 设置错峰中断标志（如果正在运行）
        self._peak_stop_requested = True
        self.stop_btn.pack_forget()
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, self.t("sim_force_stopped"))
        self.launch_btn._lbl.config(text=self.t("launch_btn"))
        self.launch_btn.config(cursor="hand2")
        if hasattr(self, 'btn_peak'):
            self.btn_peak._lbl.config(text=self.t("peak_shift_btn"))

    # ---------- 启动仿真 ----------
    def _show_auto_save_dialog(self):
        """仿真前的自动保存设置弹窗，返回设置 dict 或 None（取消）"""
        dlg = tk.Toplevel(self.root)
        dlg.title(self.t("save_settings_title"))
        dlg.geometry("440x360")
        dlg.resizable(False, False)
        dlg.config(bg="#F0F8FF")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.root.winfo_x() + (600 - 420) // 2
        y = self.root.winfo_y() + (690 - 300) // 2
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text=self.t("save_settings_title"), font=(SYSTEM_FONT, 14, "bold"),
                 bg="#2980B9", fg="white", pady=8).pack(fill="x")

        # 启用自动保存
        auto_var = tk.BooleanVar(value=bool(self._auto_save_settings))
        cb = tk.Checkbutton(dlg, text=self.t("save_auto_save"), variable=auto_var,
                            font=(SYSTEM_FONT, 11, "bold"), bg="#F0F8FF",
                            activebackground="#F0F8FF")
        cb.pack(anchor="w", padx=15, pady=(10, 2))

        # 格式选择
        tk.Label(dlg, text=self.t("save_format"), font=(SYSTEM_FONT, 10),
                 bg="#F0F8FF").pack(anchor="w", padx=20, pady=(6, 2))
        fmt_frame = tk.Frame(dlg, bg="#F0F8FF")
        fmt_frame.pack(anchor="w", padx=25)
        xlsx_var = tk.BooleanVar(value=True)
        docx_var = tk.BooleanVar(value=False)
        pdf_var = tk.BooleanVar(value=False)
        tk.Checkbutton(fmt_frame, text="Excel (.xlsx)", variable=xlsx_var,
                       font=(SYSTEM_FONT, 10), bg="#F0F8FF",
                       activebackground="#F0F8FF").pack(anchor="w")
        tk.Checkbutton(fmt_frame, text="Word (.docx)", variable=docx_var,
                       font=(SYSTEM_FONT, 10), bg="#F0F8FF",
                       activebackground="#F0F8FF").pack(anchor="w")
        tk.Checkbutton(fmt_frame, text="PDF (.pdf)", variable=pdf_var,
                       font=(SYSTEM_FONT, 10), bg="#F0F8FF",
                       activebackground="#F0F8FF").pack(anchor="w")

        # 保存路径
        tk.Label(dlg, text=self.t("save_path_label"), font=(SYSTEM_FONT, 10),
                 bg="#F0F8FF").pack(anchor="w", padx=20, pady=(8, 2))
        path_frame = tk.Frame(dlg, bg="#F0F8FF")
        path_frame.pack(anchor="w", padx=20)
        default_path = os.path.join(os.path.expanduser("~"), "Desktop", "仿真报告")
        path_var = tk.StringVar(value=default_path)
        tk.Entry(path_frame, textvariable=path_var, font=(SYSTEM_FONT, 10),
                 width=32).pack(side="left")
        tk.Button(path_frame, text=self.t("save_browse"), font=(SYSTEM_FONT, 9),
                  command=lambda: self._browse_export_path(path_var, "xlsx")
                  ).pack(side="left", padx=4)

        result = {"confirmed": False}

        def _on_start():
            if auto_var.get():
                fmts = []
                if xlsx_var.get(): fmts.append("xlsx")
                if docx_var.get(): fmts.append("docx")
                if pdf_var.get(): fmts.append("pdf")
                if not fmts:
                    messagebox.showwarning("未选格式", "请至少选择一种保存格式", parent=dlg)
                    return
                result["settings"] = {
                    "enabled": True,
                    "formats": fmts,
                    "path": path_var.get().strip(),
                }
            else:
                result["settings"] = {"enabled": False}
            result["confirmed"] = True
            dlg.destroy()

        bf = tk.Frame(dlg, bg="#F0F8FF")
        bf.pack(pady=(16, 8))
        self._make_btn(bf, self.t("save_launch"), font=(SYSTEM_FONT, 12, "bold"),
                       bg="#2980B9", fg="white", active_bg="#1F6DA0", active_fg="white",
                       command=_on_start, padx=20, pady=5,
                       pack_side="left", pack_padx=10)
        self._make_btn(bf, self.t("cancel"), font=(SYSTEM_FONT, 10),
                       bg="#DDD", fg="#333", active_bg="#BBB", active_fg="#333",
                       command=dlg.destroy, padx=14, pady=4,
                       pack_side="left", pack_padx=10)

        dlg.wait_window()
        return result.get("settings") if result["confirmed"] else None

    def _launch_simulation(self):
        if self.current_user is None:
            messagebox.showwarning(self.t("not_login_warn"), self.t("not_login_msg"))
            return

        errors = self.validate_params()
        if errors:
            messagebox.showwarning(self.t("param_invalid"), "\n".join(errors))
            return

        # 弹出自动保存设置窗口
        auto_save = self._show_auto_save_dialog()
        if auto_save is None:  # 用户取消
            return
        self._auto_save_settings = auto_save

        # 参数上限检查：超过建议值弹确认框
        limit_warnings = []
        ticks_val = int(self.entry_ticks.get())
        students_val = int(self.entry_students.get())
        lang = self.lang
        if ticks_val > _PARAM_LIMITS["ticks"]:
            limit_warnings.append(_PARAM_LIMIT_WARNINGS.get(lang, _PARAM_LIMIT_WARNINGS["zh_CN"])["ticks"])
        if students_val > _PARAM_LIMITS["students"]:
            limit_warnings.append(_PARAM_LIMIT_WARNINGS.get(lang, _PARAM_LIMIT_WARNINGS["zh_CN"])["students"])
        if limit_warnings:
            msg = self.t("limit_warn_msg") + "\n\n"
            msg += "\n".join(f"  • {w}" for w in limit_warnings)
            msg += "\n\n" + self.t("limit_warn_confirm")
            if not messagebox.askyesno(self.t("limit_warn_title"), msg):
                self._auto_save_settings = None
                return

        open_canteens = [n for n, v in self._canteen_vars.items() if v.get()]
        if len(open_canteens) < 1:
            messagebox.showwarning(self.t("no_canteen"), self.t("no_canteen"))
            return

        config_dict = {
            'max_ticks': int(self.entry_ticks.get()),
            'student_count': int(self.entry_students.get()),
            'canteen_count': len(open_canteens),
            'spawn_rate': float(self.entry_spawn.get()),
            'enable_visualization': self.enable_viz_var.get(),
            'open_canteens': open_canteens,
            'stagger_enabled': self.stagger_var.get(),
            'algorithm_params': {
                'distance_weight': self.alpha_var.get(),
                'queue_weight': self.beta_var.get(),
            },
            'lang': self.lang,
            'sim_start_time': self.entry_start_time.get().strip(),
            '_config_data': self._config_data,  # JSON 导入的完整配置（含坐标覆盖）
        }

        enable_viz = config_dict['enable_visualization']
        self.launch_btn._lbl.config(text=self.t("launching"))
        self.launch_btn.config(cursor="watch")
        self.stop_btn.pack(side="left", padx=2, pady=2)
        self.export_frame.pack_forget()  # 新仿真隐藏导出按钮
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, self.t("running_msg"))
        self.root.update()

        if enable_viz:
            # 可视化模式：必须在主线程运行（Matplotlib TkAgg 后端要求）
            def _run_viz():
                try:
                    from main import run_simulation_from_gui
                    result = run_simulation_from_gui(config_dict)
                    self._display_result(result)
                except Exception as e:
                    self._display_result({
                        'success': False, 'statistics': None, 'summary': None,
                        'error': str(e)
                    })
            # 用 after 延迟让 GUI 先更新状态，再切到可视化
            self.root.after(200, _run_viz)
        else:
            def run_in_thread():
                try:
                    from main import run_simulation_from_gui
                    result = run_simulation_from_gui(config_dict)
                    self.root.after(0, lambda: self._display_result(result))
                except Exception as e:
                    self.root.after(0, lambda: self._display_result({
                        'success': False, 'statistics': None, 'summary': None,
                        'error': str(e)
                    }))
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()

    def _display_result(self, result):
        self.stop_btn.pack_forget()
        self.launch_btn._lbl.config(text=self.t("launch_btn"))
        self.launch_btn.config(cursor="hand2")
        self.result_text.delete("1.0", tk.END)
        self.export_frame.pack_forget()

        if result['success']:
            # 存引擎引用供导出
            if result.get('engine'):
                self._last_engine = result['engine']
                self.export_frame.pack(fill="x", pady=(4, 0))
                # 自动保存（如果用户在弹窗中启用了）
                aset = self._auto_save_settings
                if aset and aset.get("enabled"):
                    self._auto_save(result['engine'], aset)
                self._auto_save_settings = None  # 跑完重置，下次默认不勾选
            stats = result['statistics']
            self.result_text.insert(tk.END, "=" * 50 + "\n")
            self.result_text.insert(tk.END, f"  {self.t('sim_complete')}\n")
            self.result_text.insert(tk.END, "=" * 50 + "\n\n")
            if stats:
                self.result_text.insert(tk.END, self.t("stats_title") + "\n")
                for key, value in stats.items():
                    if isinstance(value, float):
                        self.result_text.insert(tk.END, f"  {key}: {value:.2f}\n")
                    else:
                        self.result_text.insert(tk.END, f"  {key}: {value}\n")
            if result.get('summary'):
                self.result_text.insert(tk.END, "\n" + result['summary'])
        else:
            self.result_text.insert(tk.END, "=" * 50 + "\n")
            self.result_text.insert(tk.END, f"  {self.t('sim_failed')}\n")
            self.result_text.insert(tk.END, "=" * 50 + "\n\n")
            self.result_text.insert(tk.END,
                                    f"{self.t('error')}:\n{result.get('error', '???')}\n")

    def run(self):
        self.root.mainloop()


# ====================== 入口 ======================
if __name__ == "__main__":
    init_user_file()
    app = BJTUSimulationGUI()
    app.run()
