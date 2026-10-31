# R3e代表流程：已通过预留，联运与读档待验

日期：2026-10-31。运行源码`8131d5b`，本机群星4.5.2（eb95），只启用本Mod。基线`2293.10.11.sav`保留，未推进游戏日期。

## 实际结果

在首都“交界都市”通过正常决议点击“工程物资：预留”。入口随后变为“投入当地施工”和“撤回”，殖民地出现物资标记。用户已另存`2293.10.11-r3e-reserve.sav`，共2,573,589字节；读取压缩存档核对得到：

| 内容 | 结果 |
| --- | --- |
| 玩家／首都 | 国家0，行星3 |
| 当地物资 | `acs_supply_reserved`一份，永久有效；`acs_owner3`指向国家0 |
| 矿物 | 141356.52464 → 140856.52464，恰好扣500 |
| 合金 | 145000 → 144900，恰好扣100 |
| 能源／消费品 | 均未变化 |
| 测试设施 | 配给仓与联运换装站各一座 |
| 联运端点 | 始发端、接收端均未登记 |

完整结构化数据见[存档核对](artifact_civilization_r3e_reserve_save_2026-10-31.json)。这是存档文件读取，不是引擎实际载回；没有把它写成读档通过。

## 受控前置

本回合统一使用已跟踪的原生窗口／扫描码守卫，不混用Computer Use。控制台实际成功提交以下三条命令（输入文件有两个前导空格）：

```text
research_technology tech_artifact_distributed_supply_storage
research_technology tech_artifact_intercolony_transport
effect add_building=building_artifact_distribution_depot add_building=building_artifact_intercolony_terminal
```

第三条作用于当时选中的首都。研究和设施属于受控前置，不代表自然研发、建造队列或建筑平衡通过；没有设置物资、端点或完成标记，也没有调用预留效果替代正常决议。

第一次输入仓储研究时仍为中文输入法组合，未提交。只清理本轮已知输入，在空行切换一次模式后，完整英文输入和回车生效。后续两条也有实际执行回显。自动开关控制台成功；不能据此声称所有输入框或所有焦点情形已修复。

## 停止点与接手

登记始发端前发生失焦，守卫未发送点击；重新置前后截图过期，第二次也未发送。试玩已经超过约20分钟预算，停止继续排障。自动改存档名同样因失焦停止，用户完成一次另存。没有待补交命令；旧输入文件不是执行队列。

下一次安排阶段试玩时，从新档现有首都一份物资接续即可：登记始发端、另一殖民地建立前置并登记接收端、转运并当地使用。只需一次最终新状态实际读档。不要重做已通过的研究输入或预留扣费。R3f源码开发可以继续。

目前未验：两端转运、当地交付、返还、精炼／共治运行、设施失效／转让引擎回调、整条链实际读档与自然平衡。源代码检查覆盖不替代这些结果。

## 本机证据

- 新档：`C:\Users\Admin\Documents\Paradox Interactive\Stellaris\save games\_-258619271\2293.10.11-r3e-reserve.sav`。
- 无损备份：`runtime-backups/r3e-reserve-2026-10-31/`；本轮命令文件已移入同目录，仅作历史证据。
- `tools/desktop/r3e_storage_submitted.png`、`r3e_transport_submitted.png`、`r3e_capital_facilities_submitted.png`：三条命令实际回显。
- `tools/desktop/r3e_capital_decisions_bottom.png`与`r3e_reserve_selected.png`：预留前后入口。
- `tools/desktop/r3e_role_list.png`与`r3e_save_dialog.png`：未登记端点及另存前的停止位置。

截图、游戏存档和`runtime-backups`不随Git克隆；报告及结构化结果随Git保存。既有旧存档舰队／第三方预设警告和标签补丁未重载的限制，继续保留在[R3e检查点](artifact_civilization_r3e_checkpoint_2026-10-31.json)。
