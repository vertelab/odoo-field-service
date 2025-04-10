from odoo import models, fields, api

class FieldServiceOrder(models.Model):
    _inherit = 'fieldservice.order'

    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'Critic')
    ], string='Allvarlighetsgrad')

    reaction_time = fields.Float(string='Reaction Time', compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_avg = fields.Float(string='Reaction Time (AVG)',group_operator='avg', compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_min = fields.Float(string='Reaction Time (MIN)',group_operator='min', compute='_compute_reaktion_time', store=True, help='Time in hours')
    reaction_time_max = fields.Float(string='Reaction Time (MAX)',group_operator='max', compute='_compute_reaktion_time', store=True, help='Time in hours')
    
    time_until_work_start = fields.Float(string='Resolution Time', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    time_until_work_start_avg = fields.Float(group_operator='avg', string='Resolution Time (AVG)', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    time_until_work_start_max = fields.Float(group_operator="max", string='Resolution Time (MAX)', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    time_until_work_start_min = fields.Float(group_operator="min", string='Resolution Time (MIN)', compute='_compute_time_until_work_start', store=True, help='Time in hours')
    
    time_until_work_done = fields.Float(string='Arrival Time', compute='_compute_time_until_work_done', store=True, help='Time in hours')
    time_until_work_done_avg = fields.Float(group_operator='avg', string='Arrival Time (AVG)', compute='_compute_time_until_work_done', store=True, help='Time in hours')
    time_until_work_done_min = fields.Float(group_operator='min', string='Arrival Time (MIN)', compute='_compute_time_until_work_done', store=True, help='Time in hours')
    time_until_work_done_max = fields.Float(group_operator='max', string='Arrival Time (MAX)', compute='_compute_time_until_work_done', store=True, help='Time in hours')

    @api.depends('create_date', 'date_start')
    def _compute_time_until_work_start(self):
        for record in self:
            if record.create_date and record.date_start:
                record.time_until_work_start = (record.date_start - record.create_date).total_seconds() / 3600
            else:
                record.time_until_work_start = 0.0
            record.time_until_work_start_avg = record.time_until_work_start
            record.time_until_work_start_min = record.time_until_work_start
            record.time_until_work_start_max = record.time_until_work_start

    
    @api.depends('date_start', 'date_end')
    def _compute_time_until_work_done(self):
        for record in self:
            if record.date_start and record.date_end:
                record.time_until_work_done = (record.date_end - record.date_start).total_seconds() / 3600
            else:
                record.time_until_work_done = 0.0
            record.time_until_work_done_avg = record.time_until_work_done
            record.time_until_work_done_max = record.time_until_work_done
            record.time_until_work_done_min = record.time_until_work_done


    
    @api.depends('create_date', 'planned_start_datetime')
    def _compute_reaktion_time(self):
        for record in self:
            if record.create_date and record.planned_start_datetime:
                record.reaction_time = (record.planned_start_datetime - record.create_date).total_seconds() / 3600
            else:
                record.reaction_time = 0.0
            record.reaction_time_avg = record.reaction_time
            record.reaction_time_min = record.reaction_time
            record.reaction_time_max = record.reaction_time