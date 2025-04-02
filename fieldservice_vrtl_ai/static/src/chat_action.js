// /**@odoo-module **/


import publicWidget from "@web/legacy/js/public/public_widget";


odoo.define('fieldservice_vrtl_ai.suggestion_button', function (require) {
        "use strict";

        // const publicWidget = require('web.public.widget');

        publicWidget.registry.SuggestionButton = publicWidget.Widget.extend({
            selector: '.suggestion-btn',
            events: {
                'click': '_onSuggestionClick',
            },

            _onSuggestionClick: function (event) {
                event.preventDefault(); 
                const message = $(event.currentTarget).data('msg'); 

                this._rpc({
                    model: 'mail.channel',
                    method: 'send_message',
                    args: [self.channel_id.id, { content: message }],
                }).then(function () {
                    console.log("Message sent successfully!");
                }).catch(function (error) {
                    console.error("Failed to send message:", error);
                });
            },
        });

        return publicWidget.registry.SuggestionButton;
    });
