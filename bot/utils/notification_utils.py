import logging
import os

from telegram import Bot, ParseMode
from telegram.utils.request import Request

from bot.models import Participant, TimeSlot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

request = Request(connect_timeout=0.5, read_timeout=1.0)
bot = Bot(
    request=request,
    token=TELEGRAM_TOKEN,
)


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace("\\", "")
    characters = [".", "+", "(", ")", "-", "!", "=", "_"]
    for character in characters:
        text = text.replace(character, f"\{character}")
    return text


def notify_teams(teams=None):

    for team in teams:
        pm = team["pm"]
        students = list(team["students"])

        project_name = team["pm_timeslot"].team_project
        start_date = team["pm_timeslot"].team_project.date_start.strftime("%d.%m.%Y")
        end_date = team["pm_timeslot"].team_project.date_end.strftime("%d.%m.%Y")
        call_time = team["pm_timeslot"].time_slot.strftime("%H:%M")

        team_text = "\n".join([f"{student}" for student in students])
        pm_text = (
            f"{pm.name}, поздравляем! Для вас сформировалась группа студентов\n"
            f"Проект: *{project_name}*\n"
            f"Даты: *{start_date} - {end_date}*\n"
            f"Команда: \n*{team_text}*\n"
            f"Созвон в: *{call_time}*"
        )
        logger.error(f"{pm.tg_id=} :: {pm_text=}")
        try:
            bot.send_message(
                chat_id=pm.tg_id,
                text=escape_characters(pm_text),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except:
            pass

        for student in students:
            if student.tg_id:
                my_team = students[:]
                my_team.remove(student)
                user_id = student.tg_id
                team_txt = "\n".join([f"{teammate}" for teammate in my_team])
                text = (
                    f"На неделе с *{start_date} - {end_date}* вы участвуете в команде с:\n*{team_txt}*\n"
                    f"Ваш ПМ: *{pm}*\n"
                    f"Проект: *{project_name}*\n"
                    f"Созвон в: *{call_time}*"
                )
                logger.info(f"{user_id=} :: {text=}")
                try:
                    bot.send_message(
                        chat_id=user_id,
                        text=escape_characters(text),
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
                except:
                    pass


def notify_free_students(students=None):
    if not students.exists():
        return
    for student in students:
        if student.tg_id:
            user_id = student.tg_id
            free_slots = (
                TimeSlot.objects.filter(
                    participant__role=Participant.PRODUCT_MANAGER,
                    team_project__isnull=True,
                )
                .values("time_slot")
                .distinct()
            )
            free_times = [slot["time_slot"].strftime("%H:%M") for slot in free_slots]
            text = (
                f"*{student.name}*, к сожалению на выбранные вами слоты времени группы не нашлось.\n"
                f"Есть слоты на *{', '.join(free_times)}*\n"
                f"Если какой-то из них устраивает Вас, добавьте его в список возможных /start\n"
                f"Спасибо!"
            )
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=escape_characters(text),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
            except:
                pass
            logger.info(student)
