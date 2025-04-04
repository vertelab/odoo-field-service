import logging
import markdown
from markupsafe import Markup
import markdownify
import re
import ast
import re
import ast
import json

from langchain_core.messages import AIMessage
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    followup_question_ids = fields.One2many('followup.questions', 'mail_message_id')


class FollowupQuestions(models.Model):
    _name = "followup.questions"
    _description = "Followup Questions"
    _rec_name = 'question'

    question = fields.Char(string="Question")
    mail_message_id = fields.Many2one("mail.message")


class MailChannel(models.Model):
    _inherit = 'discuss.channel'


    def _extract_followup_questions(self, message):
        """
        Extract follow-up questions from a message that contains a JSON dictionary.
        Handles both regular JSON and JSON inside backticks.

        Args:
            message (str): The message containing JSON follow-up questions

        Returns:
            tuple: (cleaned_message, followup_questions_dict)
        """
        # First, try to find JSON in backticks
        backtick_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        backtick_match = re.search(backtick_pattern, message, re.DOTALL)

        if backtick_match:
            json_text = backtick_match.group(1)
            try:
                followup_questions = json.loads(json_text)
                # Remove the extracted JSON with backticks from the content
                cleaned_message = re.sub(backtick_pattern, '', message, flags=re.DOTALL).strip()
                return cleaned_message, followup_questions
            except json.JSONDecodeError:
                pass  # If JSON parsing fails, fall back to the next method

        # If no valid JSON in backticks, try to find raw JSON
        raw_json_pattern = r"(\{(?:[^{}]|(?:\{[^{}]*\}))*\})"
        raw_match = re.search(raw_json_pattern, message, re.DOTALL)

        if raw_match:
            json_text = raw_match.group(1)
            try:
                followup_questions = json.loads(json_text)
                # Remove the extracted raw JSON from the content
                cleaned_message = message.replace(json_text, '').strip()
                return cleaned_message, followup_questions
            except json.JSONDecodeError:
                # Try with ast.literal_eval as a fallback
                try:
                    followup_questions = ast.literal_eval(json_text)
                    cleaned_message = message.replace(json_text, '').strip()
                    return cleaned_message, followup_questions
                except Exception:
                    pass
        # If we get here, no valid JSON was found
        return message, None

    def _process_message_post(self, bot_response):
        message_content, _ = super()._process_message_post(bot_response)
        content, followup_questions = self._extract_followup_questions(message_content)
        return content, followup_questions

    def _postprocess_message_post(self, message_id, followup_questions):
        message_id.followup_question_ids = [(0, 0, {'question': value}) for key, value in followup_questions.items()]