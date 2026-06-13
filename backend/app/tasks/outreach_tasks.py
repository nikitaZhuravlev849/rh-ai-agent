import logging

logger = logging.getLogger(__name__)


def send_communication(communication_id: int):
    logger.info(f"[stub] send_communication({communication_id}) — запустите Celery для авторассылки")


send_communication.delay = lambda comm_id: logger.info(f"[stub] delay send_communication({comm_id})")


def send_scheduled_followups():
    logger.info("[stub] send_scheduled_followups — запустите Celery")


def generate_followup_communication(original_comm_id: int):
    logger.info(f"[stub] generate_followup_communication({original_comm_id})")


generate_followup_communication.delay = lambda comm_id: None
