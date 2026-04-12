from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger
import random
from typing import List

class MepinPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化默认配置
        self.default_enabled = False
        self.default_probability = 10
        self.default_monitored_users: List[str] = []
        
        # 从插件存储加载配置，若无则使用默认值
        self.enabled = self.get_kv_data("enabled", self.default_enabled)
        self.probability = self.get_kv_data("probability", self.default_probability)
        self.monitored_users = self.get_kv_data("monitored_users", self.default_monitored_users)
        
        # 确保概率在合理范围内
        if not isinstance(self.probability, int) or self.probability < 0 or self.probability > 100:
            self.probability = self.default_probability
            self.save_config()
        
        # 确保 monitored_users 是列表类型
        if not isinstance(self.monitored_users, list):
            self.monitored_users = self.default_monitored_users
            self.save_config()
            
        logger.info(f"[mepin] 插件初始化完成：enabled={self.enabled}, probability={self.probability}, monitored_users={self.monitored_users}")

    async def save_config(self):
        """保存当前配置到插件存储"""
        try:
            self.put_kv_data("enabled", self.enabled)
            self.put_kv_data("probability", self.probability)
            self.put_kv_data("monitored_users", self.monitored_users)
            logger.info("[mepin] 配置已保存至存储")
        except Exception as e:
            logger.error(f"[mepin] 保存配置失败: {str(e)}")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """监听群消息，当监控用户发言时，按概率回复“没品”"""
        # 如果功能未开启，直接忽略
        if not self.enabled:
            return
            
        sender_id = event.get_sender_id()
        
        # 如果发送者不在监控列表中，忽略
        if sender_id not in self.monitored_users:
            return
            
        # 生成随机数，判断是否触发回复
        if random.randint(0, 100) <= self.probability:
            try:
                await event.send(event.plain_result("没品"))
                logger.info(f"[mepin] 已为用户 {sender_id} 触发“没品”回复")
            except Exception as e:
                logger.error(f"[mepin] 发送回复失败: {str(e)}")

    @filter.command("mepin toggle")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def toggle_mepin(self, event: AstrMessageEvent):
        """开启或关闭“没品”回复功能"""
        self.enabled = not self.enabled
        self.save_config()
        
        status = "✅" if self.enabled else "❌"
        message = f"{status} “没品”功能已{'开启' if self.enabled else '关闭'}。"
        yield event.plain_result(message)
        logger.info(f"[mepin] 管理员 {event.get_sender_id()} 已{'开启' if self.enabled else '关闭'}“没品”功能")

    @filter.command("mepin setprob")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def set_probability(self, event: AstrMessageEvent, prob: int):
        """设置触发“没品”回复的概率（0-100）"""
        if not isinstance(prob, int) or prob < 0 or prob > 100:
            yield event.plain_result("❌ 概率必须是 0 到 100 之间的整数。")
            return
            
        self.probability = prob
        self.save_config()
        yield event.plain_result(f"🎯 “没品”触发概率已设置为 {prob}%。")
        logger.info(f"[mepin] 管理员 {event.get_sender_id()} 将概率设置为 {prob}%")

    @filter.command("mepin list")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def list_monitored_users(self, event: AstrMessageEvent):
        """查看当前被监控的用户列表"""
        if not self.monitored_users:
            yield event.plain_result("👥 当前监控用户列表为空。")
        else:
            user_list_str = "\n".join([f"- {user}" for user in self.monitored_users])
            yield event.plain_result(f"👥 当前监控用户列表（共 {len(self.monitored_users)} 人）：\n{user_list_str}")
        logger.info(f"[mepin] 管理员 {event.get_sender_id()} 查看了监控用户列表")

    @filter.command("mepin add")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def add_monitored_user(self, event: AstrMessageEvent, user_id: str):
        """添加一个用户到监控列表"""
        if not user_id or not isinstance(user_id, str):
            yield event.plain_result("❌ 请提供有效的用户 ID。")
            return
            
        if user_id in self.monitored_users:
            yield event.plain_result(f"ℹ️ 用户 {user_id} 已在监控列表中，无需重复添加。")
        else:
            self.monitored_users.append(user_id)
            self.save_config()
            yield event.plain_result(f"➕ 用户 {user_id} 已加入监控列表。")
            logger.info(f"[mepin] 管理员 {event.get_sender_id()} 添加用户 {user_id} 到监控列表")

    @filter.command("mepin remove")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def remove_monitored_user(self, event: AstrMessageEvent, user_id: str):
        """从监控列表中移除一个用户"""
        if not user_id or not isinstance(user_id, str):
            yield event.plain_result("❌ 请提供有效的用户 ID。")
            return
            
        if user_id in self.monitored_users:
            self.monitored_users.remove(user_id)
            self.save_config()
            yield event.plain_result(f"➖ 用户 {user_id} 已从监控列表中移除。")
            logger.info(f"[mepin] 管理员 {event.get_sender_id()} 从监控列表中移除用户 {user_id}")
        else:
            yield event.plain_result(f"❓ 用户 {user_id} 不在监控列表中。")

    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("[mepin] 插件正在关闭...")