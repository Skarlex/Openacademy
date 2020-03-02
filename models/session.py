
import random
from datetime import timedelta
from odoo import models, fields, api , exceptions , _


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    price_per_hour = fields.Integer(help="Price") # new
    total = fields.Integer(help="total", compute='calc_total') #new

    price_session = fields.Float(string="Price for Session")
    total_price_sessions = fields.Float(string="Total")

    state = fields.Selection([
        ('draft', "DRAFT"),
        ('confirm', "CONFIRM"),
        ('validate', "VALIDATE"),
    ], default='draft', string='State')
    button_clicked = fields.Boolean(string='Button clicked')
    invoice_ids = fields.One2many("account.move", "session_id")
    invoice_count = fields.Integer(string="count invoice", compute="_compute_invoice_count")



    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=['|', ('instructor', '=', True),
                                            ('category_id.name', 'ilike', "Teacher")])

    course_id = fields.Many2one('openacademy.course',
                                ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    end_date = fields.Date(string="End Date", store=True,
        compute='_get_end_date', inverse='_set_end_date')

    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)

    date = fields.Date(required=True, default=fields.Date.context_today) #new
    # state = fields.Selection([('brouillon', "brouillon"),
    #     ('en_cours', "En_Cours"),
    #     ('validé', "Validé"),
    # ], default = 'brouillon')
    # def act_brouillon(self):
    #     self.state = 'brouillon'
    # def act_en_cours(self):
    #     self.state = 'en cours'
    # def act_valide(self):
    #     self.state = 'validé'



    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")


    
    def test_action_serveur(self):
        for r in self:
            r.name = "Test New Name"

    def brouillon_progressbar(self):
        self.write({
            'state': 'brouillon'
        })

    def confirm_progressbar(self):
        self.write({
            'state': 'confirm'
        })


    def facturer(self):
        self.button_clicked = True
        data = {
            'session_id': self.id,
            'partner_id': self.instructor_id.id,
            'type': 'in_invoice',
            # 'partner_shipping_id' : self.instructor_id.address,
            'invoice_date': self.date
        }
        # line = {
        #     'name': self.name,
        #     # 'quantity': self.duration,
        #     'price_unit': self.price_per_hour
        # }
       # invoice1 = self.env['account.move.line'].create(line)
        invoice2 = self.env['account.move'].create(data)

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }

        action['context'] = context
        return action

    # This function is triggered when the user clicks on the button 'Done'
    def validate_progressbar(self):
        self.write({
            'state': 'validate',
        })



    def calc_total(self):
        self.total = self.duration * self.price_per_hour

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def _compute_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('session_id', '=', self.id)])

    def _calc_total_sessions(self):
        self.total_price_sessions = sum(self.price_session)

    def _calculate_total(self):
        # bundle = self.total_price_sessions
        # self.lst_price = 0.0
        # for each in bundle:
        #     self.lst_price += each.tm_sum
        for order in self:
            comm_total = 10
            for line in self.total_price_sessions:
                comm_total += line.price_session
            order.update({'total_price_sessions': comm_total})
