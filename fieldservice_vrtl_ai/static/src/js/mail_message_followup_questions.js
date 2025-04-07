// JavaScript Component
import {
    Component,
    markup,
    onMounted,
    onPatched,
    onWillDestroy,
    onWillUpdateProps,
    toRaw,
    useChildSubEnv,
    useEffect,
    onWillStart,
    useRef,
    useState,
    onRendered
} from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { Message } from "@mail/core/common/message";
import { discussComponentRegistry } from "@mail/core/common/discuss_component_registry";

patch(Message.prototype, {
    setup() {
        super.setup(...arguments);
        this.action = useService("action");

        this.state = useState({
            isLastMessage: false,
            followupQuestions: [],
            loading: true,
            lastMessageId: null,
            currentThreadId: null,
            hasInitialized: false // Flag to track initialization status
        });

        // Get reference to the questions container for scrolling
        this.questionsRef = useRef("questionsContainer");

        // Use onWillStart to ensure async operations before first render
        onWillStart(async () => {
            if (!this.state.hasInitialized) {
                await this.initializeThread();
                this.state.hasInitialized = true;
            }
        });

        // Use effect to fetch questions only when lastMessageId changes AND we're the last message
        useEffect(
            () => {
                if (this.state.lastMessageId && this.state.isLastMessage && !this.state.followupQuestions.length) {
                    this.fetchFollowupQuestions();
                }
            },
            () => [this.state.lastMessageId, this.state.isLastMessage]
        );
    },

    async initializeThread() {
        try {
            // Get current thread ID from message
            let threadId = null;

            if (this.message && this.message.thread) {
                threadId = this.message.thread.id;
            } else if (this.message && this.message.model === 'discuss.channel') {
                threadId = this.message.res_id;
            }

            if (!threadId) return;

            this.state.currentThreadId = threadId;

            // Get the last message ID directly from server
            const lastMessages = await rpc("/web/dataset/call_kw", {
                model: "mail.message",
                method: "search_read",
                args: [[["model", "=", "discuss.channel"], ["res_id", "=", threadId]]],
                kwargs: {
                    fields: ["id"],
                    limit: 1,
                    order: "id DESC",
                },
            });

            if (lastMessages && lastMessages.length > 0) {
                this.state.lastMessageId = lastMessages[0].id;

                // Check if current message is the last message
                this.state.isLastMessage = (this.message.id === this.state.lastMessageId);

                // Log ONLY if this is the last message - this prevents multiple logs
                if (this.state.isLastMessage) {
                    console.log(`Thread ${threadId} - Last message ID: ${this.state.lastMessageId}`);
                }
            }
        } catch (error) {
            console.error("Error initializing thread:", error);
        }
    },

    async fetchFollowupQuestions() {
        try {
            if (!this.state.lastMessageId || !this.state.isLastMessage) return;

            this.state.loading = true;

            const followupQuestions = await rpc("/web/dataset/call_kw", {
                model: "followup.questions",
                method: "search_read",
                args: [[["mail_message_id", "=", this.state.lastMessageId]]],
                kwargs: {
                    fields: ["id", "question"],
                },
            });

            this.state.followupQuestions = followupQuestions || [];

            // Log ONLY ONCE after fetching the questions
            console.log("Followup questions for last message:", this.state.followupQuestions);
        } catch (error) {
            console.error("Error fetching followup questions:", error);
            this.state.followupQuestions = [];
        } finally {
            this.state.loading = false;
        }
    },

    scrollToQuestions() {
        // Scroll to the questions container with a small delay to ensure rendering is complete
        setTimeout(() => {
            if (this.questionsRef.el) {
                this.questionsRef.el.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            } else {
                // Fallback: try to scroll to the message itself
                const messageElement = this.el || document.querySelector(`[data-message-id="${this.message.id}"]`);
                if (messageElement) {
                    messageElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'nearest'
                    });
                }
            }
        }, 100);
    },


    onFollowupAction(ev, question) {
        ev.preventDefault();

        // Post the question as a new message
        const channelId = this.state.currentThreadId;
        if (channelId && question) {
            console.log(`Posting question "${question.question}" to channel ${channelId}`);

            rpc("/mail/message/post", {
                thread_model: "discuss.channel",
                thread_id: channelId,
                post_data: {
                    body: question.question,
                    message_type: "comment",
                },
            }).then(() => {
                console.log("Question posted successfully");

                // Force scroll to the bottom of the thread after a small delay
                setTimeout(() => {
                    // Try to get the thread container and scroll to bottom
                    const threadContainer = document.querySelector('.o_ThreadView_bottomPanel');
                    if (threadContainer) {
                        threadContainer.scrollTop = threadContainer.scrollHeight;
                    }
                }, 300);
            }).catch(error => {
                console.error("Error posting question:", error);
            });
        }
    }
});