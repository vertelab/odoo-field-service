from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFieldServiceSLA(TransactionCase):
    """Tests for fieldservice_sla.

    The module has two time fields that are easy to confuse:

      allowed_hours  required, used by the stored compute
                     fieldservice.order.sla.sla_breached and by
                     fieldservice.order.sla_breached
      time_within    optional, used by check_all_slas and by the
                     assigned_date simulation

    Both are exercised below so the difference stays visible.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_new = cls.env['fieldservice.stage'].search(
            [('name', '=', 'New')], limit=1)
        cls.stage_done = cls.env['fieldservice.stage'].search(
            [('name', '=', 'Completed')], limit=1)
        if not cls.stage_new:
            cls.stage_new = cls.env['fieldservice.stage'].create(
                {'name': 'New'})
        if not cls.stage_done:
            cls.stage_done = cls.env['fieldservice.stage'].create(
                {'name': 'Completed'})

        cls.partner = cls.env['res.partner'].create(
            {'name': 'SLA Test Customer'})

        cls.sla_low = cls.env['fieldservice.sla'].create({
            'name': 'Low severity SLA',
            'severity_level': 'low',
            'stage_id': cls.stage_done.id,
            'allowed_hours': 24.0,
            'time_within': 24.0,
            'sla_time_type': 'all_hours',
        })
        cls.sla_high = cls.env['fieldservice.sla'].create({
            'name': 'High severity SLA',
            'severity_level': 'high',
            'stage_id': cls.stage_done.id,
            'allowed_hours': 4.0,
            'time_within': 4.0,
            'sla_time_type': 'all_hours',
        })

    def _make_order(self, severity='low', stage=None):
        return self.env['fieldservice.order'].create({
            'name': 'SLA test order',
            'partner_id': self.partner.id,
            'severity_level': severity,
            'stage_id': (stage or self.stage_new).id,
        })

    # ------------------------------------------------------------------
    # Order <-> SLA linking
    # ------------------------------------------------------------------

    def test_onchange_severity_level_links_matching_sla(self):
        """_onchange_severity_level links only SLAs of the same severity."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()

        self.assertEqual(len(order.order_sla_ids), 1)
        self.assertEqual(order.order_sla_ids.sla_id, self.sla_low)

    def test_onchange_severity_level_high_links_high_sla(self):
        order = self._make_order(severity='high')
        order._onchange_severity_level()

        self.assertEqual(len(order.order_sla_ids), 1)
        self.assertEqual(order.order_sla_ids.sla_id, self.sla_high)

    def test_onchange_replaces_previous_links(self):
        """Changing severity must not accumulate links."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        self.assertEqual(len(order.order_sla_ids), 1)

        order.severity_level = 'high'
        order._onchange_severity_level()

        self.assertEqual(len(order.order_sla_ids), 1)
        self.assertEqual(order.order_sla_ids.sla_id, self.sla_high)

    def test_onchange_without_matching_sla_clears_links(self):
        """A severity with no SLA configured leaves the order unlinked."""
        order = self._make_order(severity='medium')
        order._onchange_severity_level()

        self.assertFalse(order.order_sla_ids)

    def test_create_does_not_apply_onchange(self):
        """An onchange only runs in the UI.

        This is the behaviour that made offer-generated work orders arrive
        without any SLA row; elevata_offer calls the onchange explicitly
        after create(). Guarding it here keeps the assumption explicit.
        """
        order = self._make_order(severity='low')

        self.assertFalse(order.order_sla_ids)

        order._onchange_severity_level()
        self.assertEqual(len(order.order_sla_ids), 1)

    # ------------------------------------------------------------------
    # stage_id write -> sla_end_date
    # ------------------------------------------------------------------

    def test_stage_write_sets_sla_end_date(self):
        """Reaching the SLA's target stage stamps sla_end_date."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        self.assertFalse(link.sla_end_date)

        order.write({'stage_id': self.stage_done.id})

        self.assertTrue(link.sla_end_date)

    def test_stage_write_to_other_stage_leaves_end_date_empty(self):
        """A stage that is not the SLA target does not stamp the date."""
        other = self.env['fieldservice.stage'].create({'name': 'In Progress'})
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids

        order.write({'stage_id': other.id})

        self.assertFalse(link.sla_end_date)

    def test_stage_write_does_not_overwrite_existing_end_date(self):
        """The first time the target is reached wins."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        first_stamp = fields.Datetime.now() - timedelta(days=1)
        link.sla_end_date = first_stamp

        order.write({'stage_id': self.stage_done.id})

        self.assertEqual(link.sla_end_date, first_stamp)

    # ------------------------------------------------------------------
    # duration_to_sla and sla_breached
    # ------------------------------------------------------------------

    def test_duration_to_sla_all_hours(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=10)

        self.assertAlmostEqual(link.duration_to_sla, 10.0, places=2)

    def test_duration_to_sla_zero_without_end_date(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids

        self.assertEqual(link.duration_to_sla, 0.0)

    def test_sla_breached_false_within_allowed_hours(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=2)

        self.assertFalse(link.sla_breached)

    def test_sla_breached_true_beyond_allowed_hours(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)

        self.assertTrue(link.sla_breached)

    def test_link_breach_compares_against_time_within(self):
        """The link's stored compute reads time_within."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=10)

        self.assertFalse(link.sla_breached)

        self.sla_low.time_within = 1.0
        link.invalidate_recordset()
        self.assertTrue(link.sla_breached)

    def test_order_breach_compares_against_allowed_hours(self):
        """The order's compute reads allowed_hours."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=10)

        self.assertFalse(order.sla_breached)

        self.sla_low.allowed_hours = 1.0
        order.invalidate_recordset()
        self.assertTrue(order.sla_breached)

    def test_link_and_order_breach_can_disagree(self):
        """Known inconsistency in the module, pinned so it cannot drift silently.

        fieldservice.order.sla._compute_sla_breached compares
        duration_to_sla against sla_id.time_within, while
        fieldservice.order._compute_sla_breached compares it against
        sla_id.allowed_hours. With the two fields set differently the link
        and its order report opposite answers for the same order.

        This test documents the current behaviour. If the module is ever
        changed to use one field for both, this test should start failing —
        which is the point.
        """
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=10)

        # 10 h elapsed: allowed_hours 24 says fine, time_within 1 says breached
        self.sla_low.allowed_hours = 24.0
        self.sla_low.time_within = 1.0
        link.invalidate_recordset()
        order.invalidate_recordset()

        self.assertTrue(link.sla_breached)
        self.assertFalse(order.sla_breached)

    def test_order_sla_breached_aggregates_links(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)

        self.assertTrue(order.sla_breached)

    # ------------------------------------------------------------------
    # assigned_date simulation
    # ------------------------------------------------------------------

    def test_assigned_date_all_hours(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids

        expected = order.create_date + timedelta(hours=24)
        self.assertAlmostEqual(
            (link.assigned_date - expected).total_seconds(), 0, delta=60)

    def test_assigned_date_false_without_time_within(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        self.sla_low.time_within = 0.0

        self.assertFalse(link.assigned_date)

    # ------------------------------------------------------------------
    # check_all_slas
    # ------------------------------------------------------------------

    def test_check_all_slas_stamps_target_reached_date(self):
        order = self._make_order(severity='low', stage=self.stage_done)
        order._onchange_severity_level()
        link = order.order_sla_ids

        result = self.sla_low.check_all_slas()

        self.assertTrue(link.target_reached_date)
        self.assertEqual(result['reached'], 1)

    def test_check_all_slas_does_not_restamp_target_reached_date(self):
        order = self._make_order(severity='low', stage=self.stage_done)
        order._onchange_severity_level()
        link = order.order_sla_ids
        first_stamp = fields.Datetime.now() - timedelta(days=1)
        link.target_reached_date = first_stamp

        self.sla_low.check_all_slas()

        self.assertEqual(link.target_reached_date, first_stamp)

    def test_check_all_slas_flags_breach_past_time_within(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)

        result = self.sla_low.check_all_slas()

        self.assertTrue(link.sla_breached)
        self.assertEqual(result['breached'], 1)

    def test_check_all_slas_clears_breach_when_back_in_range(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)
        self.sla_low.check_all_slas()
        self.assertTrue(link.sla_breached)

        link.sla_end_date = order.create_date + timedelta(hours=1)
        self.sla_low.check_all_slas()

        self.assertFalse(link.sla_breached)

    # ------------------------------------------------------------------
    # notify_sla_breach
    # ------------------------------------------------------------------

    def test_notify_sla_breach_posts_once(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)
        self.sla_low.check_all_slas()

        before = len(order.message_ids)
        result = self.sla_low.notify_sla_breach()

        self.assertEqual(result['notified'], 1)
        self.assertTrue(link.breach_notified)
        self.assertEqual(len(order.message_ids), before + 1)

        # Second run must not post again
        result = self.sla_low.notify_sla_breach()
        self.assertEqual(result['notified'], 0)
        self.assertEqual(len(order.message_ids), before + 1)

    def test_notify_sla_breach_clears_flag_when_no_longer_breached(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)
        self.sla_low.check_all_slas()
        self.sla_low.notify_sla_breach()
        self.assertTrue(link.breach_notified)

        link.sla_end_date = order.create_date + timedelta(hours=1)
        self.sla_low.check_all_slas()
        result = self.sla_low.notify_sla_breach()

        self.assertFalse(link.breach_notified)
        self.assertEqual(result['cleared'], 1)

    def test_notify_sla_breach_does_not_change_breach_flag(self):
        """Notification is reporting only; the flag belongs to check_all_slas."""
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)
        self.sla_low.check_all_slas()
        self.assertTrue(link.sla_breached)

        self.sla_low.notify_sla_breach()

        self.assertTrue(link.sla_breached)

    # ------------------------------------------------------------------
    # Aggregates on fieldservice.sla
    # ------------------------------------------------------------------

    def test_order_sla_count(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()

        self.assertEqual(self.sla_low.order_sla_count, 1)

    def test_avg_duration_to_sla(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=10)

        self.assertAlmostEqual(
            self.sla_low.avg_duration_to_sla, 10.0, places=1)

    def test_breached_flag_on_sla(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()
        link = order.order_sla_ids
        link.sla_end_date = order.create_date + timedelta(hours=48)

        self.assertTrue(self.sla_low.breached)

    def test_action_view_linked_orders(self):
        order = self._make_order(severity='low')
        order._onchange_severity_level()

        action = self.sla_low.action_view_linked_orders()

        self.assertEqual(action['res_model'], 'fieldservice.order')
        self.assertIn(order.id, action['domain'][0][2])

    # ------------------------------------------------------------------
    # set_stage_by_name
    # ------------------------------------------------------------------

    def test_set_stage_by_name(self):
        self.sla_low.set_stage_by_name('Completed')
        self.assertEqual(self.sla_low.stage_id, self.stage_done)

    def test_set_stage_by_name_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.sla_low.set_stage_by_name('No Such Stage')

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    def test_allowed_hours_is_required(self):
        with self.assertRaises(Exception):
            self.env['fieldservice.sla'].create({
                'name': 'Missing allowed hours',
                'severity_level': 'low',
                'stage_id': self.stage_done.id,
            })

    def test_severity_level_is_required_on_sla(self):
        with self.assertRaises(Exception):
            self.env['fieldservice.sla'].create({
                'name': 'Missing severity',
                'stage_id': self.stage_done.id,
                'allowed_hours': 8.0,
            })

    def test_severity_level_is_required_on_order(self):
        with self.assertRaises(Exception):
            self.env['fieldservice.order'].create({
                'name': 'Order without severity',
                'partner_id': self.partner.id,
            })
