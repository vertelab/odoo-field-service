# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FieldServiceOrderLifecycle(models.Model):
    """Stage transitions on the work order.

    Moved here from elevata_fsm_flow, where they had no business being: an
    order that can be assigned, scheduled, started and closed is generic
    field service, not elevator service. Keeping them in an Elevata module
    meant any other customer had to install the elevator module to get a
    working order lifecycle, and it forced fieldservice_account_analytic to
    depend on Elevata for a view that called these buttons.

    The guards are deliberate: an order cannot be assigned without someone
    assigned to it, and cannot be scheduled without a start time. Without
    them the stage would say one thing and the data another.
    """

    _inherit = 'fieldservice.order'

    def _stage(self, xmlid):
        """Look up a stage without raising when it is missing.

        raise_if_not_found=False keeps the buttons working on databases
        where a stage has been renamed or removed — the button then does
        nothing rather than crashing the form.
        """
        return self.env.ref(xmlid, raise_if_not_found=False)

    def action_assign(self):
        for order in self:
            if not order.requested_employee_ids:
                raise ValidationError(
                    _("Cannot move to Assigned until 'Assigned To' is filled in")
                )
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_assigned')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_schedule(self):
        for order in self:
            if not order.planned_start_datetime:
                raise ValidationError(
                    _("Cannot move to Planning until a planned start is set")
                )
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_planning')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_start(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_ongoing')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_complete(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_completed')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def action_cancel(self):
        stage = self._stage('fieldservice_vrtl.fieldservice_stage_cancelled')
        if not stage:
            return False
        return self.write({'stage_id': stage.id})

    def _auto_assign_stage(self):
        """Move the order when the data that justifies the move arrives.

        Called from write() when planned_start_datetime or
        requested_employee_ids change: a scheduled order should not sit in
        New, and an assigned one should not either.
        """
        new_stage = self.env.ref(
            'fieldservice_vrtl.fieldservice_stage_new', raise_if_not_found=False
        )
        assigned_stage = self._stage(
            'fieldservice_vrtl.fieldservice_stage_assigned'
        )
        scheduled_stage = self._stage(
            'fieldservice_vrtl.fieldservice_stage_planning'
        )
        for order in self:
            # Only move forward from New or Assigned. An order already in
            # Planning or beyond is left alone: setting a start time on an
            # order that is already ongoing must not drag it backwards.
            if new_stage and order.stage_id not in (new_stage, assigned_stage):
                continue
            if order.planned_start_datetime and scheduled_stage:
                order.stage_id = scheduled_stage
            elif order.requested_employee_ids and assigned_stage:
                order.stage_id = assigned_stage

    def write(self, vals):
        """Trigger the stage move when the justifying data changes."""
        res = super().write(vals)
        if (vals.get('requested_employee_ids')
                or vals.get('planned_start_datetime')):
            self._auto_assign_stage()
        return res
