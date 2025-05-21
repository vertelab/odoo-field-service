import re
import ast
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from langchain.schema import AIMessage, HumanMessage, SystemMessage

_logger = logging.getLogger(__name__)

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

class AIQuestSession(models.Model):
    _inherit = 'ai.quest.session'

    ai_type = fields.Selection(
        selection_add=[('fieldservice-order', 'Chat with servicorder')],
        ondelete={'fieldservice-order': 'cascade'}
    )


class AIAgent(models.Model):
    _inherit = "ai.agent"

    ai_type = fields.Selection(
        selection_add=[('fieldservice-order', 'Chat with serviceorder')], ondelete={'fieldservice-order': 'cascade'})


    def agent_extra_context(self, quest, record=None):
        res = super().agent_extra_context(quest=quest, record=record)
        if self.ai_type == "fieldservice-order":
            service_order = self.env['fieldservice.order'].search([('ai_quest_id', '=', quest.id)], limit=1)
            if service_order:
                res['Service Title'] = service_order.name
                res['Reference number'] = service_order.order_number
                res['Service Order Description'] = service_order.description
                res['The manufacturer or brand of the product'] = service_order.brand
                res['The model name or number of the product'] = service_order.model
                res['The unique serial number of the product'] = service_order.serial_number
                res['The product number or part number'] = service_order.product_number
                res['Any specific marking or label on the product'] = service_order.marking
                res['The date when the product was purchased'] = service_order.purchase_date
                res['Work instructions'] = service_order.work_instructions
                res['Directions to location'] = service_order.location_instructions
        return res

    def trigger_prompt(self, session=False, debug=False, quest=False, **kwargs):
        """
          Single agent prompting from quest.code
         
          result = agents[0].prompt(
                   session=session,
                   debug=quest.debug,
                   message=html2plaintext(message.body),)

        """

        self.last_run = fields.Datetime.now()

        topic = kwargs.get('topic', kwargs.get('message', ''))
        if session:
            quest = session.ai_quest_id
        else:
            quest = self.env.ref('ai_agent.ai_quest_test')
        debug = kwargs.get('debug', quest.debug)
        if debug:
            _logger.error(f"{self=}{session=} {quest=} {self.last_run} {kwargs=}")
            session.add_message(f"Agent {self.name} {topic=}")

        if not self.ai_agent_llm_id:
            if debug:
                self.log_message("No LLM")
            raise UserError("No LLM")

        use_lang = f"Use language {self.env.user.lang}" if quest.use_personal_lang else ''

        system_message = SystemMessage(
            content=f"""You are an agent with specific responsibilities.
                Role: {self.ai_role}
                Goal: {self.ai_goal}
                Backstory: {self.ai_backstory}

                
                {self._extra_context(quest)}
                
                Instructions:
                - Provide thorough, complete responses
                - Use available tools and memory when needed
                - Stay focused on your specific role
                - Guidelines and instructions: {quest.description}
        {use_lang}
                """
        )
        prompt = self.ai_prompt_template
        prompt = prompt.format_map(SafeDict(self.extra_context(quest)))
        messages = [system_message, HumanMessage(content=topic), HumanMessage(content=prompt)]

        if debug:
            self.log_message(f"Agent  {self.name} prompt {messages=}")
            _logger.debug(f"Agent {self.name} {messages=}")
        try:
            response = self.ai_agent_llm_id.invoke(messages, session=session, quest=quest, agent=self, debug=debug)
        except Exception as e:
            _logger.error(f"Error in agent {self.name}: {str(e)}")
            self.log_message(f"Error in agent {self.name}: {str(e)}\n{traceback.format_exc()}")
            return {
                "messages": [
                    AIMessage(
                        content=f"Error occurred in agent {self.name}: {str(e)}\n{traceback.format_exc()}  ",
                        name=self.name.replace(' ', '_').replace(',', '').replace('.', '')
                    )
                ]
            }
        session.save_messages(response)
        return response


class AIQuest(models.Model):
    _inherit = "ai.quest"

    ai_type = fields.Selection(
        selection_add=[('fieldservice-order', 'Chat with serviceorder')],
        ondelete={'fieldservice-order': 'cascade'}
    )

    def custom_extract_json(self, json_str):
        # Find JSON-like content within triple backticks
        pattern = r'(\{.*\})'
        match = re.search(pattern, json_str, re.DOTALL)

        if match:
            result = match.group(1)
            result = eval(result)
            return result
            
        return False
        
        
        
