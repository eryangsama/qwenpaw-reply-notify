# QwenPaw 回复通知插件 v2.0

当 QwenPaw 的 AI 回复完成时，播放一个柔和的提示音。

> v2.0：只保留声音，无弹窗，响应更快、零干扰。

## 文件结构

```
qwenpaw-reply-notify/
├── README.md
├── hooks/
│   ├── __init__.py
│   └── notify_done_hook.py    ← Hook，注册到 react_agent.py
└── scripts/
    ├── notify_done.py          ← 播放逻辑（MCI）
    └── assets/
        ├── notify.wav          ← 提示音（PCM WAV）
        └── qwenpaw_done.png   ← 头像（预留）
```

## 安装步骤

### 1. 复制文件

将 `hooks/` 和 `scripts/` 覆盖到 QwenPaw 工作区：

```
C:\Users\yang\.qwenpaw\workspaces\default\
```

### 2. 注册 Hook

在 `react_agent.py` 的 `_register_workspace_hook()` 方法中添加：

```python
workspace_hooks_dir = working_dir / "hooks"
if workspace_hooks_dir.exists():
    sys.path.insert(0, str(workspace_hooks_dir.parent))
    try:
        from hooks import NotifyDoneHook
        self.register_instance_hook("post_reply", "notify_done", NotifyDoneHook())
    except ImportError:
        pass
```

### 3. 重启 QwenPaw

daemon 重新加载后生效。

## v2.0 更新

| | v1 | v2 |
|---|---|---|
| 通知方式 | 头像弹窗 + 提示音 | 仅提示音 |
| 响应延迟 | 3~8 秒 | < 1 秒 |
| 弹窗 | tkinter（3秒关闭） | 无 |
| 播放 | winsound（常失败） | Windows MCI（稳定） |

**修复内容：**
- 移除 tkinter 弹窗，消除窗口闪动
- 改用 Windows MCI API (`mciSendString`)，支持 MP3/WAV
- 增加 `_has_pending_tools()` 判断，只在最终回复时触发

## 自定义提示音

替换 `scripts/assets/notify.wav` 即可，推荐 PCM WAV（44.1kHz / 16bit / 双声道）。

## 技术原理

```
ReAct Agent
    ↓ post_reply hook（每步都触发）
NotifyDoneHook
    ↓ _has_pending_tools() 过滤（只保留最终回复）
notify_done()
    ↓ 后台线程
mciSendString open → play → 3秒后 close
```
