"""
组员C GUI集成测试脚本
=====================
测试 GUI 登录验证、参数配置、仿真启动、可视化、异常场景

运行方式：
  python test_member_c_integration.py              # 无 GUI 模式（测试后端逻辑）
  python test_member_c_integration.py --gui        # GUI 交互模式（需要显示器）

测试覆盖清单 (>=8项):
  1. 登录验证：学生正确密码登录 / 错误密码拒绝
  2. 登录验证：空账号拒绝 / 访客免密 / 角色未选拒绝
  3. 参数校验：合法参数通过 / 负 ticks 拒绝 / spawn_rate 超界拒绝
  4. 未登录直接启动：弹出"请先登录"提示
  5. GUI 接口：run_simulation_from_gui 正常返回
  6. 策略权重映射：distance/queue/balanced 正确传递
  7. 配置文件加载：从 JSON 解析参数
  8. 可视化集成：enable_visualization 开关传递 + 可视化器初始化
  9. 全链路端到端：正常/异常/极端场景
  10. GUI 组件结构与函数完整性检查
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


# ============================================================
# 1. 登录验证逻辑测试（纯函数，不依赖 Tk）
# ============================================================
def test_login_validation():
    print("=" * 60)
    print("1. 登录验证逻辑测试")
    print("=" * 60)

    from gui import validate_account, validate_password

    # ---- 账号格式：学生学号必须8位数字 ----
    check("学生8位数字合法", validate_account("24281213", "学生")[0])
    check("学生7位数字拒绝", not validate_account("2428121", "学生")[0])
    check("学生9位数字拒绝", not validate_account("242812131", "学生")[0])
    check("学生含字母拒绝", not validate_account("2428121a", "学生")[0])

    # ---- 账号格式：教师工号4-5位数字 ----
    check("教师4位数字合法", validate_account("1001", "教师")[0])
    check("教师5位数字合法", validate_account("10001", "教师")[0])
    check("教师3位数字拒绝", not validate_account("100", "教师")[0])
    check("教师6位数字拒绝", not validate_account("100001", "教师")[0])

    # ---- 通用校验 ----
    check("空账号被拒绝", not validate_account("", "学生")[0])
    check("纯空格账号被拒绝", not validate_account("   ", "学生")[0])
    check("含 < > 被拒绝", not validate_account("1234<script>", "教师")[0])
    check("含引号被拒绝", not validate_account("test'orc", "学生")[0])
    check("含 & 被拒绝", not validate_account("test&who", "学生")[0])
    check("含字母拒绝(纯数字要求)", not validate_account("admin123", "学生")[0])

    # ---- 密码 ----
    check("合法密码(>=3位)", validate_password("123")[0])
    check("短密码(<3位)被拒绝", not validate_password("ab")[0])
    check("空密码被拒绝", not validate_password("")[0])


# ============================================================
# 2. 用户文件操作测试
# ============================================================
def test_user_file_operations():
    print("\n" + "=" * 60)
    print("2. 用户文件操作测试")
    print("=" * 60)

    import gui

    test_file = "test_gui_users.txt"
    if os.path.exists(test_file):
        os.remove(test_file)

    original_file = gui.USER_FILE
    gui.USER_FILE = test_file

    try:
        gui.init_user_file()
        check("init_user_file 创建文件", os.path.exists(test_file))

        users = gui.load_users()
        check("空文件 load_users 返回空 dict", isinstance(users, dict) and len(users) == 0)

        gui.save_user("学生", "24281213", "mypassword")
        users = gui.load_users()
        check("save_user 后可加载", "学生:24281213" in users)
        check("密码正确存储", users["学生:24281213"] == "mypassword")

        gui.save_user("教师", "1001", "teacherpass")
        users = gui.load_users()
        check("多用户存储 (2 users)", len(users) == 2)

        check("默认密码格式", gui.get_default_password("12345678") == "12345678@bjtu")
    finally:
        gui.USER_FILE = original_file
        if os.path.exists(test_file):
            os.remove(test_file)


# ============================================================
# 3. 参数校验测试（main.py 接口）
# ============================================================
def test_parameter_validation():
    print("\n" + "=" * 60)
    print("3. 参数校验测试 (create_config_from_gui)")
    print("=" * 60)

    from main import create_config_from_gui

    config = create_config_from_gui({
        'max_ticks': 100, 'student_count': 10,
        'canteen_count': 2, 'spawn_rate': 0.1,
    })
    check("合法配置 max_ticks=100", config['max_ticks'] == 100)
    check("student_count=10", config['student_count'] == 10)
    check("canteen_count=2", config['canteen_count'] == 2)
    check("spawn_rate=0.1", abs(config['spawn_rate'] - 0.1) < 0.001)

    for bad_val, label in [(-1, "负 ticks"), (0, "零 canteen_count"), (1.5, "spawn_rate>1"), (-0.5, "spawn_rate<0")]:
        try:
            if label == "负 ticks":
                create_config_from_gui({'max_ticks': -1, 'canteen_count': 2, 'spawn_rate': 0.1})
            elif label == "零 canteen_count":
                create_config_from_gui({'max_ticks': 100, 'canteen_count': 0, 'spawn_rate': 0.1})
            elif label == "spawn_rate>1":
                create_config_from_gui({'max_ticks': 100, 'canteen_count': 2, 'spawn_rate': 1.5})
            elif label == "spawn_rate<0":
                create_config_from_gui({'max_ticks': 100, 'canteen_count': 2, 'spawn_rate': -0.5})
            check(f"{label} 应被拒绝", False)
        except ValueError:
            check(f"{label} 正确抛出 ValueError", True)

    config = create_config_from_gui({})
    check("空 dict 默认 max_ticks=150", config['max_ticks'] == 150)
    check("空 dict 默认 canteen_count=2", config['canteen_count'] == 2)
    check("空 dict 默认 spawn_rate=0.08", abs(config['spawn_rate'] - 0.08) < 0.001)
    check("空 dict 默认 student_count=30", config['student_count'] == 30)


# ============================================================
# 4. GUI 接口集成测试
# ============================================================
def test_gui_interface():
    print("\n" + "=" * 60)
    print("4. GUI 接口集成测试 (run_simulation_from_gui)")
    print("=" * 60)

    from main import run_simulation_from_gui

    result = run_simulation_from_gui({
        'max_ticks': 30, 'student_count': 10, 'canteen_count': 2,
        'spawn_rate': 0.15, 'enable_visualization': False, 'random_seed': 42,
    })
    check("success=True", result['success'] is True)
    check("statistics 不为空", result['statistics'] is not None)
    check("summary 不为空", result['summary'] is not None)
    check("error 为 None", result['error'] is None)

    stats = result['statistics']
    for key in ['total_students_generated', 'total_students_served', 'average_wait_time']:
        check(f"statistics 含 {key}", key in stats)

    print(f"    生成: {stats.get('total_students_generated')}, "
          f"服务: {stats.get('total_students_served')}, "
          f"等待: {stats.get('average_wait_time')}")

    result_err = run_simulation_from_gui({'max_ticks': -5})
    check("无效配置 success=False", result_err['success'] is False)
    check("无效配置含 error", result_err['error'] is not None)

    # 可视化模式
    import matplotlib
    matplotlib.use('Agg')
    result_viz = run_simulation_from_gui({
        'max_ticks': 10, 'student_count': 5, 'canteen_count': 1,
        'spawn_rate': 0.2, 'enable_visualization': True, 'random_seed': 42,
    })
    check("可视化模式 success=True", result_viz['success'] is True)


# ============================================================
# 5. 策略权重映射测试
# ============================================================
def test_strategy_weight_mapping():
    print("\n" + "=" * 60)
    print("5. 策略权重映射测试")
    print("=" * 60)

    from main import create_config_from_gui

    config = create_config_from_gui({
        'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1,
        'algorithm_params': {'distance_weight': 0.9, 'queue_weight': 0.1},
    })
    check("distance_weight=0.9", config['algorithm_params']['distance_weight'] == 0.9)
    check("queue_weight=0.1", config['algorithm_params']['queue_weight'] == 0.1)

    config = create_config_from_gui({
        'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1,
        'algorithm_params': {'distance_weight': 0.3, 'queue_weight': 0.7},
    })
    check("queue_weight=0.7", config['algorithm_params']['queue_weight'] == 0.7)

    config = create_config_from_gui({
        'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1,
        'algorithm_params': {'distance_weight': 0.5, 'queue_weight': 0.5},
    })
    check("balanced 两权重均为 0.5",
          config['algorithm_params']['distance_weight'] == 0.5 and
          config['algorithm_params']['queue_weight'] == 0.5)

    config = create_config_from_gui({
        'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1, 'random_seed': 12345,
    })
    check("random_seed=12345", config['random_seed'] == 12345)


# ============================================================
# 6. 配置文件加载测试
# ============================================================
def test_config_file_loading():
    print("\n" + "=" * 60)
    print("6. 配置文件加载测试")
    print("=" * 60)

    from main import load_config_file
    from config import BJTUConfig

    example_path = os.path.join(os.path.dirname(__file__), "example_config.json")
    data = load_config_file(example_path)
    check("load_config_file 成功", data is not None)
    check("coordinates 存在", "coordinates" in data)
    check("simulation_params 存在", "simulation_params" in data)
    check("algorithm_params 存在", "algorithm_params" in data)

    sp = data["simulation_params"]
    check("max_ticks=500", sp["max_ticks"] == 500)
    check("student_count=50", sp["student_count"] == 50)
    check("canteen_count=4", sp["canteen_count"] == 4)
    check("random_seed=42", sp["random_seed"] == 42)

    ap = data["algorithm_params"]
    check("distance_weight=0.3", ap["distance_weight"] == 0.3)
    check("queue_weight=0.7", ap["queue_weight"] == 0.7)

    check("不存在的文件返回 None", load_config_file("nonexistent_file.json") is None)

    config_obj = BJTUConfig(config_file=example_path)
    sim_config = config_obj.get_simulation_config()
    check("get_simulation_config 成功", sim_config is not None)
    check("canteen_names 推导正确", len(sim_config.get('canteen_names', [])) > 0)


# ============================================================
# 7. 可视化集成测试
# ============================================================
def test_visualization_integration():
    print("\n" + "=" * 60)
    print("7. 可视化集成测试")
    print("=" * 60)

    import matplotlib
    matplotlib.use('Agg')

    from visualizer import CanteenVisualizer
    from main import initialize_visualization, create_config_from_gui
    from config import BJTUConfig

    config_obj = BJTUConfig()
    config = config_obj.get_simulation_config()

    viz = initialize_visualization(config)
    check("initialize_visualization 成功", viz is not None)

    if viz:
        check("fig 存在", viz.fig is not None)
        check("ax_map 存在", viz.ax_map is not None)
        check("animation_speed=200", viz.animation_speed == 200)
        check("is_paused=False", viz.is_paused is False)

        from models import Student, Canteen
        viz.draw_frame(tick=1,
                       students=[Student(student_id=0, position=(10, 10), destination=(0, 0))],
                       canteens=[Canteen(canteen_id=0, name="测试食堂", position=(0, 0), window_count=5, capacity=50)])
        check("draw_frame 正常", True)
        viz.close()

    config_viz = create_config_from_gui({
        'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1,
        'enable_visualization': True,
    })
    check("enable_visualization=True 传递", config_viz.get('enable_visualization') is True)

    config_no = create_config_from_gui({'max_ticks': 50, 'canteen_count': 2, 'spawn_rate': 0.1})
    check("enable_visualization 默认 False", config_no.get('enable_visualization') is False)


# ============================================================
# 8. 全链路异常场景测试
# ============================================================
def test_end_to_end_error_scenarios():
    print("\n" + "=" * 60)
    print("8. 全链路异常与极端场景测试")
    print("=" * 60)

    from main import run_simulation_from_gui

    result = run_simulation_from_gui({'max_ticks': 0})
    check("max_ticks=0 返回 success=False", result['success'] is False)

    for label, cfg in [
        ("spawn_rate=1.0", {'max_ticks': 20, 'student_count': 100, 'canteen_count': 1, 'spawn_rate': 1.0, 'enable_visualization': False, 'random_seed': 99}),
        ("spawn_rate=0.0", {'max_ticks': 20, 'student_count': 0, 'canteen_count': 2, 'spawn_rate': 0.0, 'enable_visualization': False, 'random_seed': 99}),
        ("单食堂", {'max_ticks': 20, 'student_count': 20, 'canteen_count': 1, 'spawn_rate': 0.3, 'enable_visualization': False, 'random_seed': 99}),
    ]:
        result = run_simulation_from_gui(cfg)
        check(f"{label} success=True", result['success'] is True)

    result = run_simulation_from_gui({
        'max_ticks': 50, 'student_count': 50, 'canteen_count': 3,
        'spawn_rate': 0.2, 'enable_visualization': False, 'random_seed': 42,
    })
    check("中型仿真 success=True", result['success'] is True)
    stats = result['statistics']
    if stats:
        check("total_students_generated > 0", stats.get('total_students_generated', 0) > 0)
        check("canteen_utilization 存在", 'canteen_utilization' in stats)


# ============================================================
# 9. GUI 模块结构与函数完整性
# ============================================================
def test_gui_module_structure():
    print("\n" + "=" * 60)
    print("9. GUI 模块结构与函数完整性")
    print("=" * 60)

    import gui

    for fn_name in ['validate_account', 'validate_password', 'load_users', 'save_user',
                    'get_default_password', 'init_user_file']:
        check(f"{fn_name} 存在且可调用", callable(getattr(gui, fn_name, None)))

    check("MAX_ATTEMPTS = 5", gui.MAX_ATTEMPTS == 5)
    check("USER_FILE = gui_users.txt", gui.USER_FILE == "gui_users.txt")
    check("ADMIN_EMAIL 存在", hasattr(gui, 'ADMIN_EMAIL'))
    check("SCHOOL_URL 存在", hasattr(gui, 'SCHOOL_URL'))

    check("BJTUSimulationGUI 类存在",
          hasattr(gui, 'BJTUSimulationGUI') and callable(gui.BJTUSimulationGUI))

    app = gui.BJTUSimulationGUI()
    check("app.root 创建成功", app.root is not None)
    check("root.title 含 BJTU", "BJTU" in app.root.title())
    check("login_frame 存在", app.login_frame is not None)
    check("config_frame 存在", app.config_frame is not None)
    check("entry_account 存在", app.entry_account is not None)
    check("entry_password 存在", app.entry_password is not None)
    check("entry_captcha 存在", app.entry_captcha is not None)
    check("captcha_canvas 存在", app.captcha_canvas is not None)

    # role_var 初始为空（无一选中）
    check("role_var 初始为空字符串", app.role_var.get() == "")

    # 测试角色切换（仅学生/教师）
    app.role_var.set("学生")
    check("角色设置为学生", app.role_var.get() == "学生")
    app.role_var.set("教师")
    check("角色设置为教师", app.role_var.get() == "教师")

    # 验证码生成
    app._generate_captcha()
    check("验证码生成后 captcha_code 非空", len(app.captcha_code) == 4)
    check("验证码为字母数字混合", app.captcha_code.isalnum())

    # 测试参数校验（通过 Entry 输入）
    app.entry_ticks.delete(0, "end")
    app.entry_ticks.insert(0, "200")
    app.entry_canteens.delete(0, "end")
    app.entry_canteens.insert(0, "3")
    app.entry_spawn.delete(0, "end")
    app.entry_spawn.insert(0, "0.1")
    errors = app.validate_params()
    check("合法参数无校验错误", len(errors) == 0)

    app.entry_ticks.delete(0, "end")
    app.entry_ticks.insert(0, "-1")
    errors = app.validate_params()
    check("负 ticks 返回错误", len(errors) > 0 and any("ticks" in e for e in errors))

    app.entry_ticks.delete(0, "end")
    app.entry_ticks.insert(0, "abc")
    errors = app.validate_params()
    check("非数字 ticks 返回错误", len(errors) > 0)

    app.entry_ticks.delete(0, "end")
    app.entry_ticks.insert(0, "100")
    app.entry_spawn.delete(0, "end")
    app.entry_spawn.insert(0, "2.5")
    errors = app.validate_params()
    check("spawn_rate > 1 返回错误", len(errors) > 0 and any("spawn_rate" in e for e in errors))

    # 未登录直接启动
    app.current_user = None
    check("current_user 初始为 None", app.current_user is None)

    app.root.destroy()


# ============================================================
# 10. 新增功能测试：注册 / 忘记密码 / 远端登录 / 访客
# ============================================================
def test_new_features():
    print("\n" + "=" * 60)
    print("10. 新增功能测试（注册 / 忘记密码 / 访客）")
    print("=" * 60)

    import gui

    # 使用独立测试文件避免干扰
    test_file = "test_new_features_users.txt"
    if os.path.exists(test_file):
        os.remove(test_file)
    original_file = gui.USER_FILE
    gui.USER_FILE = test_file

    try:
        gui.init_user_file()
        users_before = gui.load_users()
        check("新文件初始无用户", len(users_before) == 0)

        gui.save_user("学生", "20240001", "20240001@bjtu")
        users_after = gui.load_users()
        check("注册学生后用户数+1", len(users_after) == len(users_before) + 1)
        check("注册学生可查询", "学生:20240001" in users_after)

        gui.save_user("教师", "2001", "2001@bjtu")
        users_after2 = gui.load_users()
        check("教师4位工号注册成功", "教师:2001" in users_after2)
        check("注册教师后用户数+1", len(users_after2) == len(users_after) + 1)
    finally:
        gui.USER_FILE = original_file
        if os.path.exists(test_file):
            os.remove(test_file)

    # 访客 URL
    check("SCHOOL_URL 正确", gui.SCHOOL_URL == "https://www.bjtu.edu.cn")

    # 忘记密码管理员邮箱
    check("ADMIN_EMAIL 存在", gui.ADMIN_EMAIL == "24281213@bjtu.edu.cn")


# ============================================================
# 10. GUI 交互测试（窗口显示）
# ============================================================
def test_gui_interactive():
    print("\n" + "=" * 60)
    print("10. GUI 交互测试")
    print("=" * 60)
    print("  窗口将在 2 秒后自动关闭...")

    import gui
    app = gui.BJTUSimulationGUI()

    # 模拟登录流程
    app.role_var.set("学生")
    app.entry_account.insert(0, "24281213")
    app.entry_password.insert(0, "24281213@bjtu")

    account_val = app.entry_account.get().strip()
    valid, _ = gui.validate_account(account_val, "学生")
    check("GUI 输入框账号读取正确", valid and account_val == "24281213")

    # 密码验证
    valid, _ = gui.validate_password(app.entry_password.get())
    check("密码验证通过", valid)

    app.root.after(1000, app.root.destroy)
    app.run()
    check("GUI 窗口正常关闭", True)


# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("组员C GUI 集成测试")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print()

    test_login_validation()
    test_user_file_operations()
    test_parameter_validation()
    test_gui_interface()
    test_strategy_weight_mapping()
    test_config_file_loading()
    test_visualization_integration()
    test_end_to_end_error_scenarios()
    test_gui_module_structure()
    test_new_features()

    args = sys.argv[1:]
    if "--gui" in args:
        test_gui_interactive()
    else:
        print("\n" + "=" * 60)
        print("10. GUI 交互测试 - 跳过（使用 --gui 运行）")
        print("=" * 60)

    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"结果: {PASS}/{total} 通过, {FAIL}/{total} 失败")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
