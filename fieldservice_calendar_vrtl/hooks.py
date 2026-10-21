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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# Tag name -> colour index. Names are the contract with the rest of the
# module; the index is what the calendar view paints.
# Tag name -> (xmlid suffix, colour index). The suffix is spelled out
# rather than derived, because the code refers to these xmlids by name.
TAGS = {
    'Planning Booked': ('planned_booked', 3),
    'Planning Not Booked': ('planned_unbooked', 2),
    'Timesheet': ('open_timesheet', 8),
    'Locked Timesheet': ('locked_timesheet', 0),
}

XMLID_PREFIX = 'fieldservice_calendar_vrtl.calendar_tag_'


def post_init_hook(env):
    """Bind this module's tag xmlids to the existing tag rows.

    calendar_event_type.name is unique, and elevata_base defines the same
    four names. Rather than create duplicates (which would fail) or depend
    on elevata_base (which would invert the module direction), the tags are
    looked up by name and this module's xmlids are pointed at them.
    """
    Tag = env['calendar.event.type']
    IMD = env['ir.model.data']

    for name, (suffix, color) in TAGS.items():
        tag = Tag.search([('name', '=', name)], limit=1)
        if not tag:
            tag = Tag.create({'name': name, 'color': color})
        xmlid = XMLID_PREFIX + suffix
        module, _, xml_name = xmlid.partition('.')
        existing = IMD.search([
            ('module', '=', module),
            ('name', '=', xml_name),
            ('model', '=', 'calendar.event.type'),
        ], limit=1)
        if existing:
            existing.res_id = tag.id
        else:
            IMD.create({
                'module': module,
                'name': xml_name,
                'model': 'calendar.event.type',
                'res_id': tag.id,
                'noupdate': True,
            })
