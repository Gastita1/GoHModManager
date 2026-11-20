# GoH 模组开发笔记（工具箱说明）

> 本文件是踩坑记录 + 工具说明。下次继续做模组前先读这里。

## 一、工具位置

```
F:\GoHModManager\tools\
  gohmod.py     通用工具（pak 解包/打包、任务注入、单位表导出、SDL 检查、TGA 转换）
  gohlint.py    深度检查（括号、实体 ID 冲突、include 缺失、标签引用）
```

调用（Python 用 DSH 自带运行时）：

```bat
"C:\Users\时雨时衣\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" F:\GoHModManager\tools\gohmod.py units ger late
```

## 二、游戏数据关键路径

```
G:\SteamLibrary\steamapps\common\Call to Arms - Gates of Hell\
  resource\gamelogic.pak        单位表、兵种、技能
  resource\map\multi.pak        联机地图（battle_zones.mi / ammunition.mi）
  resource\interface\scene.pak  单位图标 scene/unit_icon/<name>_00.tga
  resource\-vehicle.pak         载具实体
  resource\properties.pak       resupply.inc / human.ext
  localizations\*.pak           多语言
```

## 三、SDL 脚本要点（已验证）

- 任务文件：顶层 `{mission ...}`，**include 必须插在闭合 `}` 之前**（末尾追加会报 `End of SDL file expected`）
- 宏定义必须放在**顶层**，放在 `{Helpers}` 里对后续块无效
- `{Helpers ...}` 可以出现多次（原版模组就是这么注入菜单的）
- 事件必须**预注册**：`{event "xxx"}` 直接列在 `{Helpers}` 下（不能包 `{events}`）
- 触发器空条件 `{condition\n}` = 开局执行（原版 `initialize::menu` 用法）
- 图标写法（展开后）：
  ```lisp
  {icon_name
      {state hidden}        ; 必填，隐藏后用 {"reinforcement" {operation show} {name "..."}} 显示
      {text "..."}
      {image "menu/icons/xxx"}   ; 路径相对 resource 根，不带扩展名
      {hint "..."}
      {count -1} {score 0} {delay 0}
      {eventStart "click::xxx"}
  }
  ```
- 任务选项勾选框定义在 **`.info` 文件**里（不是 .mi）：
  ```lisp
  {mission_options
      {checks
          {"spawnmenu" {options "with_spawnmenu"} {selected ""}}
      }
  }
  ```
- 生成单位：`{"actor_to_waypoint" {selector {...}} {waypoint 5500} {clone} {approach "safe teleport & rotate"}}`
- 编号后处理：`{"squad_create" ...}` + `{"autoassign" ...}`
- 生成点固定 `(0,0,0)` 是崩溃根源（`Invalid placement matrix`），半径调大只降低概率

## 四、修改模组的三条路

| 方式 | 结果 |
|---|---|
| 本地 mods 目录做覆盖补丁 | ❌ 工坊模组优先级更高，覆盖不生效 |
| 直接改工坊目录文件 | ✅ 有效（先备份，模组更新后需重打） |
| 完整复制模组改名 | ✅ 有效但体积大（248 MB） |

## 五、已验证失败的方向

- 用 `{Helpers {reinforcements ...}}` 自建生成菜单：能加载、能执行触发器，但**图标不显示**
- 原版菜单的真实机制仍未破解：`main.mi` 只创建图标，实际渲染依赖其他部分（可能是 `set/panel_control` 或 interface action），尝试过复制整个 `resource/menu` 仍不显示
- 车组自动维修：引擎无维修光环、无 Lua 维修命令、AI 不会自动下车 → 不可实现

## 六、其他已确认事实

- 维修速度：`set/breed/presets/perks/skills.inc` 的 `{mechanic factor}`
- 医疗半径：`specialties.inc` 的 `{"medic" 15.0}`（数值=半径，米）
- 补给参数：`properties/resupply.inc` 的 `{radius}` `{resupplyPeriod}` `{regenerationPeriod}` `{limit}` `{mechanicResources}`
- 换弹时间：`set/stuff/*/**.pattern` 的 `("reload time" seconds(N))`；`gun.pattern` = 坦克/火炮，不要动
- 弹药物品 ID = 文件名把点换成空格（`hmgun_rus.ap.ammo` → `"hmgun_rus ap ammo"`）
- 步战图标：`scene/unit_icon/single_<role>(<faction>)_00`

## 七、工作流程（重要）

做任何模组功能前，按这个顺序：

1. **先检索**：Steam 工坊评论区、Steam 讨论区、3DM/贴吧、Reddit、B站、Skymods
   - 关键词：`地狱之门 <功能> mod`、`gates of hell <feature>`
   - 重点看：作者置顶回复、Bug 报告帖、求模组帖
2. **再查数据**：用 gohmod.py / gohlint.py 验证推测
3. **最后才逆向**：前两步没答案时再逐文件分析

教训：Super_Menu 的"菜单怎么开启"作者在评论里明确写过；
任务选项在 .info 里定义属于常见模组知识，搜索即可。
