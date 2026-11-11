# 本地候选包核对（2026-11-11）

当日最终候选取自已提交快照 `5fc48d2fefd4268541d1038c34056ce07404ee3d`，包内游戏内容与最终功能点 `332ccbc` 一致，包含 `23cf3ce` 的造境荒芜天体判定修复及 `332ccbc` 的 P04 报价预览缺目标防护。用现有 `tools/build/package_local_mod.py` 生成，ZIP 为 **32,434,472 字节**，内含 615 个游戏文件，另附启动器注册文件与安装说明。[本机最终候选 ZIP](../temp/local_mod_candidates/aemusa_artifact_user-candidate-5fc48d2fefd4.zip) · [安装说明](../docs/project/local_candidate_installation.md)

已用 Windows `Expand-Archive` 实际解压至 `temp/最终候选试装 2026-11-11 5fc48d2fefd4/独立用户资料/`。运行文件清单与上述提交的 `mod/` 一致，全部解压文件与 ZIP 内容逐项字节相同；外层注册的 `path="mod/aemusa_artifact_user"` 正确指向该中文路径下的真实目录。

从解压内容复制出字节一致的校验布局，并配套同一提交的状态登记表，运行 **一次 `check_mod`**，对照本机《群星》**Cygnus 4.5.4** 的原版资源：293 个脚本、270 个事件、2,376 个中文键，**0 错误、0 警告**。详细本地证据为同一试装目录下的 `package_verification.json` 与 `check_mod.json`。

内外描述符沿用「神器使与爱缪莎」、版本 `0.1.0`、适配声明 `4.4.*`，未修改生产描述符。本次范围为本地候选打包、中文路径解压与静态检查，该 ZIP 为本地开发候选。ZIP 和试装目录保留在已忽略的 `temp/`。
