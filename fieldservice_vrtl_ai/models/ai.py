from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError

import logging

_logger = logging.getLogger(__name__)


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

class AIQuest(models.Model):
    _inherit = "ai.quest"

    ai_type = fields.Selection(
        selection_add=[('fieldservice-order', 'Chat with serviceorder')], ondelete={'fieldservice-order': 'cascade'})


    def format_followup_response(self,result):
        _logger.warning("format_followup_response"*100)
        #ai_message = result['messages'][-1]  # Assuming AIMessage is always the last message
        # Access its content
        #ai_message_content = ai_message.content
        msg_list = result['messages'][-1].content.split("{")
        _logger.warning(f"{msg_list=}")
        clear_text = msg_list[0]
        _logger.warning(f"{clear_text=}")
        _logger.warning(f"{len(msg_list)=}")
        if len(msg_list) == 1:
           result['messages'][-1].content = clear_text
           _logger.warning(f"1{clear_text=}")
        else:
            #result['messages'][-1].content = clear_text
            json_result = "{" + msg_list[1]
            suggestion_html = self.create_suggestion_html(json_result)
            clear_text = clear_text + suggestion_html
            _logger.warning(f"2{clear_text=}")
            result['messages'][-1].content = clear_text
            
        return result
        

        
        
    def create_suggestion_html(self,json_result):
        suggestion_dict = eval(json_result)
        html_body = "<p></p><p></p><p></p><p></p>"
        for key in suggestion_dict:
            html_body += f"<p><a class='btn btn-primary' href='/follow_suggestion?channel={self.channel_id.id}&msg={suggestion_dict[key]}'>{suggestion_dict[key]}</a> </p>"
        return html_body


        
        
        
