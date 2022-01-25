import logging
import os
from datetime import datetime
from enum import Enum, auto

from django.core.management.base import BaseCommand
from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler, Updater
from telegram.utils.request import Request

import bot.management.commands._pm_conversation as pc
import bot.management.commands._student_conversation as sc
from bot.models import Participant

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

request = Request(connect_timeout=0.5, read_timeout=1.0)
bot = Bot(
    request=request,
    token=TELEGRAM_TOKEN,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class States(Enum):
    START_PM = auto()
    START_STUDENT = auto()


def keyboard_row_divider(full_list, row_width=2):
    """Divide list into rows for keyboard"""
    for i in range(0, len(full_list), row_width):
        yield full_list[i : i + row_width]


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace("\\", "")
    characters = [".", "+", "(", ")", "-", "!", "=", "_"]
    for character in characters:
        text = text.replace(character, f"\{character}")
    return text


def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text(
        f"Привет, {user.full_name if user.full_name else user.username}"
    )
    logger.info(
        f"User {user.id} :: {user.username} :: {user.first_name} started the conversation."
    )
    try:
        participant = Participant.objects.get(tg_username__contains=user.username)
    except Participant.DoesNotExist:
        update.effective_user.send_message(
            text="Простите, но Вас нет в наших списках"
            ", обратитесь к менторам Devman.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    except Participant.MultipleObjectsReturned:
        update.effective_user.send_message(
            text="Найдено более одного пользователя в списках" ", обратитесь в Devman.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    participant.tg_id = user.id
    # participant.full_name = user.full_name
    participant.save()

    if participant.role == Participant.PRODUCT_MANAGER:
        return send_first_step_pm(update, context)
    if participant.role == Participant.STUDENT:
        return send_first_step_student(update, context)


def send_first_step_pm(update: Update, context: CallbackContext) -> States:
    buttons = [
        [
            InlineKeyboardButton(
                text="Посмотреть периоды работы.", callback_data="show_period_pm"
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        text="Добро пожаловать о великий ПМ! )))", reply_markup=keyboard
    )

    return States.START_PM


def student_project(user_id):
    try:
        student = Participant.objects.get(tg_id=user_id)
        student.timeslots.filter(
            team_project__isnull=False,
            team_project__date_start__gte=datetime.now(),
        ).first()
    except Participant.DoesNotExist:
        return None


def send_first_step_student(update: Update, context: CallbackContext) -> States:
    user = update.message.from_user
    slot = student_project(user.id)
    if slot:
        project_name = slot.team_project.project.name
        call_time = slot.time_slot.strftime("%H:%M")
        pm = slot.product_manager
        start_date = slot.team_project.date_start.strftime("%d.%m.%Y")
        fin_date = slot.team_project.date_end.strftime("%d.%m.%Y")
        text = (
            f"На неделе с *{start_date} - {fin_date}* вы участвуете в проекте\n"
            f"Ваш ПМ: *{pm}*\n"
            f"Проект: *{project_name}*\n"
            f"Созвон в: *{call_time}*"
        )
        update.message.reply_text(
            text=escape_characters(text),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return ConversationHandler.END

    buttons = [
        [
            InlineKeyboardButton(
                text="Выбрать время", callback_data=sc.Consts.SELECT_TIME.value
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.message.reply_text(
        text="Добро пожаловать студент! Пора приступать к проекту!",
        reply_markup=keyboard,
    )

    return States.START_STUDENT


def cancel(update: Update, _) -> int:
    """Cancel and end the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} :: {user.id} canceled the conversation.")
    update.message.reply_text("Всего доброго!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


class Command(BaseCommand):
    """Start the bot."""

    help = "Телеграм-бот"

    def handle(self, *args, **options):
        updater = Updater(token=TELEGRAM_TOKEN)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
            ],
            states={
                States.START_PM: [pc.pm_conv],
                States.START_STUDENT: [sc.student_conv],
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
            ],
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
