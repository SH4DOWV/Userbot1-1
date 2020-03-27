# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for keeping control on who can PM you. """

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User

from userbot import (COUNT_PM, CMD_HELP, BOTLOG, BOTLOG_CHATID, PM_AUTO_BAN,
                     BRAIN_CHECKER, LASTMSG, LOGS, is_mongo_alive,
                     is_redis_alive)
from userbot.events import register, errors_handler
from userbot.modules.dbhelper import (approval, approve, block_pm, notif_state,
                                      notif_off, notif_on)

# ========================= CONSTANTS ============================
UNAPPROVED_MSG = (
    "`𝐇𝐞𝐲! 𝐐𝐮𝐞𝐬𝐭𝐨 è 𝐮𝐧 𝐦𝐞𝐬𝐬𝐚𝐠𝐠𝐢𝐨 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐨! \n\n `"
    "`𝐒𝐡𝐚𝐝𝐨𝐰 𝖓𝖔𝖓 𝖙𝖎 𝖍𝖆 𝖆𝖕𝖕𝖗𝖔𝖛𝖆𝖙𝖔 𝖆 𝖕𝖆𝖗𝖑𝖆𝖗𝖊 𝖈𝖔𝖓 𝖑𝖚𝖎. \n\n `"
    "`𝐏𝐞𝐫 𝐟𝐚𝐯𝐨𝐫𝐞, 𝐚𝐬𝐩𝐞𝐭𝐭𝐚 𝐜𝐡𝐞 𝐭𝐨𝐫𝐧𝐢, 𝐝𝐢 𝐬𝐨𝐥𝐢𝐭𝐨 𝐥𝐮𝐢 𝐚𝐩𝐩𝐫𝐨𝐯𝐚 𝐦𝐞𝐬𝐬𝐚𝐠𝐠𝐢 𝐩𝐫𝐢𝐯𝐚𝐭𝐢. \n\n `"
    "`𝐍𝐨𝐧 𝐚𝐩𝐩𝐫𝐨𝐯𝐚 𝐜𝐨𝐠𝐥𝐢𝐨𝐧𝐢 𝐨 𝐩𝐞𝐫𝐬𝐨𝐧𝐞 𝐜𝐡𝐞 𝐬𝐜𝐫𝐢𝐯𝐨𝐧𝐨 𝐬𝐞𝐧𝐳𝐚 𝐩𝐞𝐫𝐦𝐞𝐬𝐬𝐨.\n`"
     "`ɪɴᴠɪᴀ ᴘɪÙ ᴅɪ 4 ᴍᴇꜱꜱᴀɢɢɪ ꜱᴇɴᴢᴀ ᴇꜱꜱᴇʀᴇ ᴀᴘᴘʀᴏᴠᴀᴛᴏ ᴇ ᴠᴇʀʀᴀɪ ꜱᴇɢɴᴀʟᴀᴛᴏ ᴘᴇʀ ꜱᴘᴀᴍ ᴇ ʙʟᴏᴄᴄᴀᴛᴏ.`")
# =================================================================


@register(incoming=True, disable_edited=True)
@errors_handler
async def permitpm(event):
    """ Permits people from PMing you without approval. \
        Will block retarded nibbas automatically. """
    if PM_AUTO_BAN:
        if event.sender_id in BRAIN_CHECKER:
            return
        if event.is_private and not (await event.get_sender()).bot:
            if not is_mongo_alive() or not is_redis_alive():
                return
            apprv = await approval(event.chat_id)

            # This part basically is a sanity check
            # If the message that sent before is Unapproved Message
            # then stop sending it again to prevent FloodHit
            if not apprv and event.text != UNAPPROVED_MSG:
                if event.chat_id in LASTMSG:
                    prevmsg = LASTMSG[event.chat_id]
                    # If the message doesn't same as previous one
                    # Send the Unapproved Message again
                    if event.text != prevmsg:
                        # Searches for previously sent UNAPPROVED_MSGs
                        async for message in event.client.iter_messages(
                                event.chat_id,
                                from_user='me',
                                search=UNAPPROVED_MSG):
                            # ... and deletes them !!
                            await message.delete()
                        await event.reply(UNAPPROVED_MSG)
                    LASTMSG.update({event.chat_id: event.text})
                else:
                    await event.reply(UNAPPROVED_MSG)
                    LASTMSG.update({event.chat_id: event.text})

                if await notif_state() is False:
                    await event.client.send_read_acknowledge(event.chat_id)
                if event.chat_id not in COUNT_PM:
                    COUNT_PM.update({event.chat_id: 1})
                else:
                    COUNT_PM[event.chat_id] = COUNT_PM[event.chat_id] + 1

                if COUNT_PM[event.chat_id] > 4:
                    await event.respond("`Hai mandato più di 4 messaggi, "
                                        " ciò che ti ho detto di non fare.`"
                                        " `Ti reporto per spam e ti blocco.`")

                    try:
                        del COUNT_PM[event.chat_id]
                        del LASTMSG[event.chat_id]
                    except KeyError:
                        if BOTLOG:
                            await event.client.send_message(
                                BOTLOG_CHATID,
                                "Count PM is seemingly going retard, "
                                "plis restart bot!",
                            )
                        LOGS.info("CountPM wen't rarted boi")
                        return

                    await event.client(BlockRequest(event.chat_id))
                    await event.client(ReportSpamRequest(peer=event.chat_id))

                    if BOTLOG:
                        name = await event.client.get_entity(event.chat_id)
                        name0 = str(name.first_name)
                        await event.client.send_message(
                            BOTLOG_CHATID,
                            "[" + name0 + "](tg://user?id=" +
                            str(event.chat_id) + ")" +
                            " ecco un altro ritardato che non sa leggere.",
                        )


@register(disable_edited=True, outgoing=True)
@errors_handler
async def auto_accept(event):
    """ Will approve automatically if you texted them first. """
    if event.is_private:
        chat = await event.get_chat()
        if not is_mongo_alive() or not is_redis_alive():
            return
        if isinstance(chat, User):
            if await approval(event.chat_id) or chat.bot:
                return
            async for message in event.client.iter_messages(chat.id,
                                                            reverse=True,
                                                            limit=1):
                if message.from_id == (await event.client.get_me()).id:
                    await approve(chat.id)
                    if BOTLOG:
                        await event.client.send_message(
                            BOTLOG_CHATID,
                            "#AUTO-APPROVED\n" + "User: " +
                            f"[{chat.first_name}](tg://user?id={chat.id})",
                        )


@register(outgoing=True, pattern="^.notifoff$")
@errors_handler
async def notifoff(noff_event):
    """ For .notifoff command, stop getting
        notifications from unapproved PMs. """
    if not noff_event.text[0].isalpha() and noff_event.text[0] not in (
            "/", "#", "@", "!"):
        if await notif_off() is False:
            return await noff_event.edit('`Notifiche già silenziate!`')
        else:
            return await noff_event.edit("`Notifiche silenziate!`")


@register(outgoing=True, pattern="^.notifon$")
@errors_handler
async def notifon(non_event):
    """ For .notifoff command, get notifications from unapproved PMs. """
    if not non_event.text[0].isalpha() and non_event.text[0] not in ("/", "#",
                                                                     "@", "!"):
        if await notif_on() is False:
            return await non_event.edit("`Notifications ain't muted!")
        else:
            return await non_event.edit("`Notifications unmuted!`")


@register(outgoing=True, pattern="^.approve$")
@errors_handler
async def approvepm(apprvpm):
    """ For .approve command, give someone the permissions to PM you. """
    if not apprvpm.text[0].isalpha() and apprvpm.text[0] not in ("/", "#", "@",
                                                                 "!"):
        if not is_mongo_alive() or not is_redis_alive():
            await apprvpm.edit("`Database connections failing!`")
            return

        if await approve(apprvpm.chat_id) is False:
            return await apprvpm.edit("`𝘼𝙥𝙥𝙧𝙤𝙫𝙖𝙩𝙤!`")
        else:
            if apprvpm.reply_to_msg_id:
                reply = await apprvpm.get_reply_message()
                replied_user = await apprvpm.client(
                    GetFullUserRequest(reply.from_id))
                aname = replied_user.user.id
                name0 = str(replied_user.user.first_name)
                uid = replied_user.user.id

            else:
                aname = await apprvpm.client.get_entity(apprvpm.chat_id)
                name0 = str(aname.first_name)
                uid = apprvpm.chat_id

            await apprvpm.edit(
                f"[{name0}](tg://user?id={uid}) `𝘼𝙥𝙥𝙧𝙤𝙫𝙖𝙩𝙤 𝙖 𝙨𝙘𝙧𝙞𝙫𝙚𝙧𝙢𝙞 𝙞𝙣 𝙋𝙫𝙩!`")

            if BOTLOG:
                await apprvpm.client.send_message(
                    BOTLOG_CHATID,
                    "#APPROVED\n" + "User: " +
                    f"[{name0}](tg://user?id={uid})",
                )


@register(outgoing=True, pattern="^.block$")
@errors_handler
async def blockpm(block):
    """ For .block command, block people from PMing you! """
    if not block.text[0].isalpha() and block.text[0] not in ("/", "#", "@",
                                                             "!"):
        await block.edit("`Shadow non approva i tuoi messaggi in PM!`")

        if await block_pm(block.chat_id) is False:
            return await block.edit("`Approvo, prima di bloccarti.`")
        else:
            return await block.edit("`𝘿𝙞𝙨𝙖𝙥𝙥𝙧𝙤𝙫𝙖𝙩𝙤.`")

            if block.reply_to_msg_id:
                reply = await block.get_reply_message()
                replied_user = await block.client(
                    GetFullUserRequest(reply.from_id))
                aname = replied_user.user.id
                name0 = str(replied_user.user.first_name)
                await block.client(BlockRequest(replied_user.user.id))
                uid = replied_user.user.id
            else:
                await block.client(BlockRequest(block.chat_id))
                aname = await block.client.get_entity(block.chat_id)
                name0 = str(aname.first_name)
                uid = block.chat_id

            if not is_mongo_alive() or not is_redis_alive():
                await block.edit("`Database connections failing!`")
                return
            if BOTLOG:
                await block.client.send_message(
                    BOTLOG_CHATID,
                    "#BLOCKED\n" + "User: " + f"[{name0}](tg://user?id={uid})",
                )


@register(outgoing=True, pattern="^.unblock$")
@errors_handler
async def unblockpm(unblock):
    """ For .unblock command, let people PMing you again! """
    if not unblock.text[0].isalpha() and unblock.text[0] \
            not in ("/", "#", "@", "!") and unblock.reply_to_msg_id:
        if unblock.reply_to_msg_id:
            reply = await unblock.get_reply_message()
            replied_user = await unblock.client(
                GetFullUserRequest(reply.from_id))
            name0 = str(replied_user.user.first_name)
            if await approve(reply.from_id) is False:
                return await unblock.edit(
                    "`𝙉𝙤𝙣 𝙝𝙖𝙞 𝙗𝙡𝙤𝙘𝙘𝙖𝙩𝙤 𝙦𝙪𝙚𝙨𝙩𝙤 𝙐𝙩𝙚𝙣𝙩𝙚!`")
            else:
                return await unblock.edit(
                    "`ꜱʜᴀᴅᴏᴡ, 𝙩𝙞 𝙝𝙖 𝙨𝙗𝙡𝙤𝙘𝙘𝙖𝙩𝙤, 𝙤𝙧𝙖 𝙥𝙪𝙤𝙞 𝙨𝙘𝙧𝙞𝙫𝙚𝙧𝙜𝙡𝙞 𝙞𝙣 𝙋𝙫𝙩.`")

            await unblock.client(UnblockRequest(replied_user.user.id))

        if BOTLOG:
            await unblock.client.send_message(
                BOTLOG_CHATID,
                f"[{name0}](tg://user?id={replied_user.user.id})"
                " was unblocc'd!.",
            )


CMD_HELP.update({
    "pmpermit":
    "\
.approve\
\nUsage: Approve the mentioned/replied person to PM.\
\n\n.block\
\nUsage: Block the person from PMing you.\
\n\n.unblock\
\nUsage: Unblock the person so they can PM you.\
\n\n.notifoff\
\nUsage: Clear any notifications of unapproved PMs.\
\n\n.notifon\
\nUsage: Allow notifications for unapproved PMs.\
"
})
