from odoo import http
from odoo.http import request

class ChannelMessageController(http.Controller):
    @http.route('/follow_suggestion', type='http', auth='public', methods=['GET'])
    def send_message_to_channel(self, channel=None, msg=None):
        if not channel or not msg:
            return "Missing parameters: 'channel' and 'msg' are required."

        try:
            # Convert channel ID to integer
            channel_id = int(channel)

            # Get the channel record
            mail_channel = request.env['discuss.channel'].sudo().browse(channel_id)

            # Check if the channel exists
            if not mail_channel.exists():
                return f"Channel with ID {channel_id} does not exist."

            # Post the message to the channel
            mail_channel.message_post(
                body=msg,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

            #return f"Message '{msg}' successfully sent to channel {channel_id}."
        except Exception as e:
            pass
            #return f"Error: {str(e)}"