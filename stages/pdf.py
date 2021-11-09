from datetime import date

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.utils.dateformat import format as django_format

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.platypus import (
    Flowable, Frame, Image, NextPageTemplate, PageBreak, PageTemplate, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle, Preformatted
)

style_normal = PS(name='CORPS', fontName='Helvetica', fontSize=8, alignment=TA_LEFT)
style_normal_center = PS(name='CORPS', fontName='Helvetica', fontSize=8, alignment=TA_CENTER)
style_bold = PS(name='CORPS', fontName='Helvetica-Bold', fontSize=8, spaceBefore=0.3 * cm, alignment=TA_LEFT)
style_title = PS(name='CORPS', fontName='Helvetica-Bold', fontSize=12, alignment=TA_LEFT, spaceBefore=1 * cm)
style_adress = PS(name='CORPS', fontName='Helvetica', fontSize=8, alignment=TA_LEFT, leftIndent=10 * cm)
style_normal_right = PS(name='CORPS', fontName='Helvetica', fontSize=8, alignment=TA_RIGHT)
style_bold_center = PS(name="CORPS", fontName="Helvetica-Bold", fontSize=9, alignment=TA_CENTER)
style_footer = PS(name='CORPS', fontName='Helvetica', fontSize=7, alignment=TA_CENTER)
style_bold_title = PS(name="CORPS", fontName="Helvetica-Bold", fontSize=12, alignment=TA_LEFT)
style_smallx = PS(name='CORPS', fontName="Helvetica-BoldOblique", fontSize=6, alignment=TA_LEFT)

LOGO_EPC = find('img/logo_EPC.png')
LOGO_ESNE = find('img/logo_ESNE.png')
LOGO_EPC_LONG = find('img/header.gif')
LOGO_CIFOM = find('img/logo_CIFOM.png')
LOGO_CPLN = find('img/logo_CPLN.jpg')
LOGO_CPMB = find('img/logo_CPMB.png')


class HorLine(Flowable):
    """Line flowable --- draws a line in a flowable"""

    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width

    def __repr__(self):
        return "Line(w=%s)" % self.width

    def draw(self):
        self.canv.line(0, 0, self.width, 0)


class EpcBaseDocTemplate(SimpleDocTemplate):
    points = '.' * 93

    def __init__(self, filelike, title=''):
        super().__init__(
            filelike,
            pagesize=A4,
            lefMargin=2.5 * cm, bottomMargin=1 * cm, topMargin=1 * cm, rightMargin=2.5 * cm
        )
        self.page_frame = Frame(
            self.leftMargin, self.bottomMargin, self.width - 2.5, self.height - 3 * cm,
            id='first_table', showBoundary=0, leftPadding=0 * cm
        )
        self.story = []
        self.title = title

    def header(self, canvas, doc):
        canvas.saveState()
        canvas.drawImage(
            LOGO_EPC, doc.leftMargin, doc.height - 1.5 * cm, 5 * cm, 3 * cm, preserveAspectRatio=True
        )
        canvas.drawImage(
            LOGO_ESNE, doc.width - 2.5 * cm, doc.height - 1.2 * cm, 5 * cm, 3.3 * cm, preserveAspectRatio=True
        )

        # Footer
        canvas.line(doc.leftMargin, 1 * cm, doc.width + doc.leftMargin, 1 * cm)
        footer = Paragraph(settings.PDF_FOOTER_TEXT, style_footer)
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    def header_cifom(self, canvas, doc):
        canvas.saveState()
        top = doc.height - 1.5 * cm
        logo_height = 1.5 * cm
        canvas.drawImage(
            LOGO_CIFOM, doc.leftMargin, top, 1.7 * cm, logo_height, preserveAspectRatio=True
        )
        canvas.drawImage(
            LOGO_CPLN, doc.leftMargin + 2.4 * cm, top, 1.5 * cm, logo_height, preserveAspectRatio=True
        )
        canvas.drawImage(
            LOGO_CPMB, doc.leftMargin + 4.6 * cm, top, 3.6 * cm, logo_height, preserveAspectRatio=True
        )
        canvas.restoreState()

    def formating(self, text, style=style_normal, maxLineLength=25):
        return Preformatted(text, style, maxLineLength=maxLineLength)

    def add_address(self, person):
        self.story.append(Spacer(0, 2 * cm))
        self.story.append(Paragraph(person.civility, style_adress))
        self.story.append(Paragraph(person.full_name, style_adress))
        try:
            self.story.append(Paragraph(person.street, style_adress))
            self.story.append((Paragraph(person.pcode_city or '', style_adress)))
        except AttributeError:
            self.story.append(Spacer(0, 1.8 * cm))


class ChargeSheetPDF(EpcBaseDocTemplate):
    """
    Génération des feuilles de charges en pdf.
    """
    def __init__(self, out, teacher):
        self.teacher = teacher
        super().__init__(out)
        self.addPageTemplates([
            PageTemplate(id='FirstPage', frames=[self.page_frame], onPage=self.header)
        ])

    def produce(self, activities):
        self.add_address(self.teacher)
        tot_hyperplanning = activities['tot_mandats'] + activities['tot_ens']
        self.story.append(Paragraph(settings.CHARGE_SHEET_TITLE, style_bold))
        self.story.append(HorLine(450))
        self.story.append((Paragraph('Total HyperPlanning: {} pér.'.format(tot_hyperplanning), style_smallx)))
        data = [
            ["Report de l'année précédente", '{0:3d} pér.'.format(self.teacher.previous_report)],
            ['Mandats', '{0:3d} pér.'.format(activities['tot_mandats'])],
        ]

        for act in activities['mandats']:
            data.append(['    * {0} ({1} pér.)'.format(act.subject, act.period)])

        data.extend([
            ['Enseignement (coef.2)',
             '{0:3d} pér.'.format(activities['tot_ens'])],
            ['Formation continue et autres tâches',
             '{0:3d} pér.'.format(activities['tot_formation'])],
            ['Total des heures travaillées', '{0:3d} pér.'.format(activities['tot_trav']),
             '{0:4.1f} %'.format(activities['tot_trav'] / settings.GLOBAL_CHARGE_PERCENT)],
            ['Total des heures payées',
             '{0:3d} pér.'.format(activities['tot_paye']),
             '{0:4.1f} %'.format(activities['tot_paye'] / settings.GLOBAL_CHARGE_PERCENT)],
            ["Report à l'année prochaine",
             '{0:3d} pér.'.format(activities['report'])],
        ])

        t = Table(
            data, colWidths=[12 * cm, 2 * cm, 2 * cm], hAlign=TA_CENTER,
            rowHeights=(0.6 * cm), spaceBefore=0.4 * cm, spaceAfter=1.5 * cm
        )
        t.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -3), (-1, -1), 0.5, colors.black),
            ('FONT', (0, -2), (-1, -2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        self.story.append(t)

        d = 'La Chaux-de-Fonds, le {0}'.format(django_format(date.today(), 'j F Y'))
        self.story.append(Paragraph(d, style_normal))
        self.story.append(Spacer(0, 0.5 * cm))
        self.story.append(Paragraph('la direction', style_normal))

        if (activities['tot_paye'] == settings.GLOBAL_CHARGE_TOTAL and
                activities['tot_paye'] != activities['tot_trav']):
            self.story.append(Spacer(0, 1 * cm))
            d = 'Je soussigné-e déclare accepter les conditions ci-dessus pour la régularisation de mon salaire.'
            self.story.append(Paragraph(d, style_normal))
            self.story.append(Spacer(0, 1 * cm))
            self.story.append(Paragraph('Lieu, date et signature: ' + self.points, style_normal))
        self.story.append(PageBreak())
        self.build(self.story)


class UpdateDataFormPDF(EpcBaseDocTemplate):
    """
    Génération des formulaires PDF de mise à jour des données.
    """
    def __init__(self, out, return_date):
        super().__init__(out)
        self.text = (
            "Afin de mettre à jour nos bases de données, nous vous serions reconnaissant "
            "de contrôler les données ci-dessous qui vous concernent selon votre filière "
            "et de retourner le présent document corrigé et complété à votre maître de classe jusqu'au "
            "%s prochain.<br/><br/>"
            "Nous vous remercions de votre précieuse collaboration.<br/><br/>"
            "Le secrétariat"
        ) % django_format(return_date, 'l j F')
        self.underline = '__________________________________'

    def produce(self, klass):
        self.story = []
        header = open(LOGO_EPC_LONG, 'rb')
        for student in klass.student_set.filter(archived=False):
            self.story.append(Image(header, width=520, height=75))
            self.story.append(Spacer(0, 2 *cm))
            destinataire = '{0}<br/>{1}<br/>{2}'.format(student.civility, student.full_name, student.klass)
            self.story.append(Paragraph(destinataire, style_adress))
            self.story.append(Spacer(0, 2*cm))
            self.story.append(Paragraph('{0},<br/>'.format(student.civility), style_normal))
            self.story.append(Paragraph(self.text, style_normal))
            self.story.append(Spacer(0, 2*cm))

            data = [['Données enregistrées', 'Données corrigées et/ou complétées']]
            t = Table(data, colWidths=[8*cm, 8*cm])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ]))
            t.hAlign = TA_CENTER
            self.story.append(t)

            # Personal data
            data = [
                ['NOM', student.last_name, self.underline],
                ['PRENOM', student.first_name, self.underline],
                ['ADRESSE', student.street, self.underline],
                ['LOCALITE', student.pcode_city, self.underline],
                ['MOBILE', student.mobile, self.underline],
                ['CLASSE', student.klass, self.underline],
                ['', '', ''],
            ]

            # Corporation data
            if self.is_corp_required(student.klass.name):
                if student.corporation is None:
                    data.extend([
                        ["Données de l'Employeur", '', ''],
                        ['NOM', '', self.underline],
                        ['ADRESSE', '', self.underline],
                        ['LOCALITE', '', self.underline],
                        ['', '', '']
                    ])
                else:
                    data.extend([
                        ["Données de l'Employeur", '', ''],
                        ['NOM', student.corporation.name, self.underline],
                        ['ADRESSE', student.corporation.street, self.underline],
                        ['LOCALITE', student.corporation.pcode_city, self.underline],
                        ['', '', '']
                    ])

            # Instructor data
            if self.is_instr_required(student.klass.name):
                if student.instructor is None:
                    data.extend([
                        ['Données du FEE/FPP (personne de contact pour les informations)', '', ''],
                        ['NOM', '', self.underline],
                        ['PRENOM', '', self.underline],
                        ['TELEPHONE', '', self.underline],
                        ['E-MAIL', '', self.underline],
                    ])
                else:
                    data.extend([
                        ['Données du FEE/FPP (personne de contact pour les informations)', '', ''],
                        ['NOM', student.instructor.last_name, self.underline],
                        ['PRENOM', student.instructor.first_name, self.underline],
                        ['TELEPHONE', student.instructor.tel, self.underline],
                        ['E-MAIL', student.instructor.email, self.underline],
                    ])

            t = Table(data, colWidths=[3*cm, 5*cm, 8*cm])
            t.setStyle(TableStyle([
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            t.hAlign = TA_CENTER
            self.story.append(t)
            self.story.append(PageBreak())
        if len(self.story) == 0:
            self.story.append(Paragraph("Pas d'élèves dans cette classe", style_normal))

        self.build(self.story)
        header.close()

    def is_corp_required(self, klass_name):
        return any(el in klass_name for el in ['FE', 'EDS', 'EDEpe'])

    def is_instr_required(self, klass_name):
        return any(el in klass_name for el in ['FE', 'EDS'])


class CompensationForm:
    """Mixin class to host paiement formdata."""
    AMOUNT = ''
    EXPERT_MANDAT = 'EXPERT'
    MENTOR_MANDAT = 'MENTOR'
    EXPERT_ACCOUNT = '30 490 002'
    MENTOR_ACCOUNT = "30 490 002"
    OTP_EDE_PS_OTP = "CIFO01.03.02.07.02.01"
    OTP_EDE_PE_OTP = "CIFO01.03.02.07.01.01"

    def add_private_data(self, person):
        self.story.append(Spacer(0, 0.5 * cm))
        style = PS(name='Title1', fontName='Helvetica', fontSize=12, alignment=TA_CENTER)
        self.story.append(Paragraph('INDEMNISATION D’EXPERTS', style))
        self.story.append(Spacer(0, 0.2 * cm))
        data = [
            [self.formating('ECOLE :', style=style_bold), 'École Santé-social Pierre-Coullery', '', ''],
            [Paragraph('<u>COORDONNÉES DE L’EXPERT</u>', style=style_bold), '', '', ''],
            [self.formating('NOM : '), person.last_name or self.points, '', ''],
            [self.formating('Prénom :'), person.first_name or self.points, '', ''],
            [self.formating('Adresse complète :'), person.street, '', ''],
            ['', person.pcode_city if person.pcode else '', '', ''],
            ['', '', '', ''],
            [
                self.formating('Date de naissance :'),
                django_format(person.birth_date, 'j F Y') if person.birth_date else '',
                self.formating('Nationalité :'), person.nation or '',
            ],
            [
                self.formating('N° de téléphone :'), person.tel or '',
                self.formating('Si étranger, joindre copie permis de séjour', style=style_bold, maxLineLength=None), ''
            ],
            [
                self.formating('N° AVS :'), person.avs or '',
                self.formating('Employeur :'), Paragraph(person.corporation.name if person.corporation else '', style=style_normal),
            ],
            [Paragraph('<u>COORDONNÉES DE PAIEMENT</u>', style=style_bold), '', '', ''],
            [Paragraph('N° de ccp ou compte bancaire (<b>IBAN</b>) :', style_normal), person.iban or '', '', ''],
            [Paragraph('Si banque, nom et adresse de celle-ci :', style_normal), person.bank or '', '', ''],
        ]

        t = Table(data, colWidths=[4 * cm, 4 * cm, 2 * cm, 6 * cm], hAlign=TA_LEFT)
        t.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('BOX', (0, 0), (-1, 9), 0.25, colors.black),
            ('BOX', (0, 10), (-1, -1), 0.25, colors.black),
            ('SPAN', (1, 0), (-1, 0)),  # ecole
            ('TOPPADDING', (0, 0), (-1, 0), 12),  # ecole
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # ecole
            ('SPAN', (0, 1), (-1, 1)),  # coord expert
            ('SPAN', (1, 2), (-1, 2)),  # nom
            ('SPAN', (1, 3), (-1, 3)),  # prenom
            ('SPAN', (1, 4), (-1, 4)),  # adresse
            ('SPAN', (2, 6), (-1, 6)),
            ('VALIGN', (0, 9), (-1, 9), 'TOP'),  # avs / employeur
            ('SPAN', (0, 10), (-1, 10)),  # coord paiement
            ('TOPPADDING', (0, 10), (-1, 10), 8),  # coord paiement
        ]))
        self.story.append(t)
        self.story.append(Spacer(0, 0.5 * cm))

    def add_accounting_stamp(self, student, mandat=None):
        account = otp = ''
        total = self.AMOUNT
        if mandat == self.EXPERT_MANDAT:
            account = self.EXPERT_ACCOUNT
        elif mandat == self.MENTOR_MANDAT:
            account = self.MENTOR_ACCOUNT

        if student.klass.is_Ede_pe():
            otp = self.OTP_EDE_PE_OTP
        elif student.klass.is_Ede_ps():
            otp = self.OTP_EDE_PS_OTP

        self.story.append(Spacer(0, 0.5 * cm))
        if mandat == self.EXPERT_MANDAT:
            data = [
                ['Indemnités', 'Fr.'],
                ['Frais de déplacement', 'Fr.'],
                ['Repas', 'Fr.'],
                ['TOTAL', 'Fr.'],
            ]
            t = Table(
                data, colWidths=[4.5 * cm, 3 * cm], hAlign=TA_CENTER,
                spaceBefore=0.5 * cm, spaceAfter=0.2 * cm
            )
            t.setStyle(TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('LINEBELOW', (1, 2), (2, 2), 0.5, colors.black),
                    ('LINEBELOW', (1, 3), (2, 3), 0.5, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                ]
            ))
            self.story.append(t)
        else:
            self.story.append(Spacer(0, 2 * cm))

        self.story.append(Spacer(0, 1.5 * cm))
        self.story.append(Paragraph(
            f'Veuillez indiquer l’OTP (champ obligatoire): {otp}',
            style_normal
        ))
        self.story.append(Spacer(0, 1.5 * cm))
        self.story.append(Paragraph(
            'Date et signature de la direction de l’établissement ou du/de la responsable',
            style_normal
        ))


class ExpertEdeLetterPdf(CompensationForm, EpcBaseDocTemplate):
    reference = 'ASH/val'
    title = 'Travail de diplôme'
    resp_filiere, resp_genre = settings.RESP_FILIERE_EDE
    part1_text = """
        {expert_civility},<br/><br/>
        Vous avez accepté de fonctionner comme expert{expert_accord} pour un {title_lower} de l’un-e de nos
        étudiant-e-s. Nous vous remercions très chaleureusement de votre disponibilité.<br/><br/>
        En annexe, nous avons l’avantage de vous remettre le travail de {student_civility_full_name},
        ainsi que la grille d’évaluation commune aux deux membres du jury.<br/><br/>
        La soutenance de ce travail de diplôme se déroulera le:<br/><br/>
    """
    part2_text = """
        <br/>
        L’autre membre du jury sera {internal_expert_civility} {internal_expert_full_name}, {internal_expert_role} dans notre école.<br/>
        <br/>
        Par ailleurs, nous nous permettons de vous faire parvenir en annexe le formulaire «Indemnisation d’experts aux examens»
        que vous voudrez bien compléter au niveau des «données privées / coordonnées de paiement» et nous retourner dans les meilleurs délais.
        <br/><br/>
        Restant à votre disposition pour tout complément d’information et en vous remerciant de
        l’attention que vous porterez à la présente, nous vous prions d’agréer, {expert_civility}, l’assurance de notre considération distinguée.<br/>
        <br/><br/><br/>
    """

    def __init__(self, out, exam):
        self.exam = exam
        super().__init__(out)
        self.addPageTemplates([
            PageTemplate(id='FirstPage', frames=[self.page_frame], onPage=self.header),
            PageTemplate(id='ISOPage', frames=[self.page_frame], onPage=self.header_cifom),
        ])

    def exam_data(self):
        return {
            'expert': self.exam.external_expert,
            'internal_expert': self.exam.internal_expert,
            'date_exam': self.exam.date_exam,
            'room': self.exam.room,
        }

    def produce(self):
        exam_data = self.exam_data()
        self.add_address(exam_data['expert'])

        header_text = """
            <br/><br/><br/>
            La Chaux-de-Fonds, le {current_date}<br/>
            N/réf.: {ref}<br/>
            <br/><br/><br/>
            <strong>{title}</strong>
            <br/><br/><br/>
        """
        self.story.append(Paragraph(header_text.format(
            current_date=django_format(date.today(), 'j F Y'),
            ref=self.reference,
            title=self.title,
        ), style_normal))

        self.story.append(Paragraph(self.part1_text.format(
            title_lower=self.title.lower(),
            expert_civility=exam_data['expert'].civility,
            expert_accord=exam_data['expert'].adjective_ending,
            student_civility_full_name=self.exam.student.civility_full_name,
        ), style_normal))

        date_text = "<br/>{0} à l'Ecole Santé-social Pierre-Coullery, salle {1}<br/><br/>"
        self.story.append(Paragraph(date_text.format(
            django_format(exam_data['date_exam'], 'l j F Y à H\hi'),
            exam_data['room'],
        ), style_bold_center))

        self.story.append(Paragraph(self.part2_text.format(
            internal_expert_civility=exam_data['internal_expert'].civility,
            internal_expert_full_name=exam_data['internal_expert'].full_name,
            internal_expert_role=exam_data['internal_expert'].role,
            expert_civility=exam_data['expert'].civility,
        ), style_normal))

        footer_text = """
            {lela} responsable de filière:<br/>
            <br/><br/>
            {resp_filiere}
            <br/><br/><br/>
            Annexes: ment.
        """
        self.story.append(Paragraph(footer_text.format(
            lela='Le' if self.resp_genre == 'M' else 'La',
            resp_filiere=self.resp_filiere,
        ), style_normal))

        # ISO page
        self.story.append(NextPageTemplate('ISOPage'))
        self.story.append(PageBreak())

        self.add_private_data(exam_data['expert'])

        self.story.append(Paragraph(
            "Mandat: Soutenance de {0} {1}, classe {2}".format(
                self.exam.student.civility, self.exam.student.full_name, self.exam.student.klass
            ), style_normal
        ))
        self.story.append(Paragraph(
            "Date de l'examen : {}".format(django_format(exam_data['date_exam'], 'l j F Y')), style_normal
        ))
        self.story.append(Spacer(0, 2 * cm))

        self.add_accounting_stamp(self.exam.student, self.EXPERT_MANDAT)

        self.build(self.story)


class ExpertEdsLetterPdf(ExpertEdeLetterPdf):
    reference = 'BAH/ner'
    title = 'Travail final'
    resp_filiere, resp_genre = settings.RESP_FILIERE_EDS
    part1_text = """
        {expert_civility},<br/><br/>
        Vous avez accepté de fonctionner comme expert{expert_accord} pour un {title_lower} de l'un-e de nos
        étudiant-e-s. Nous vous remercions très chaleureusement de votre disponibilité.<br/><br/>
        En annexe, nous avons l'avantage de vous remettre le travail de {student_civility_full_name},
        ainsi que diverses informations sur le cadre de cet examen et la grille d'évaluation
        commune aux deux membres du jury.<br/><br/>
        La soutenance de ce travail de diplôme se déroulera le:<br/><br/>
    """


class CompensationPDFForm(CompensationForm, EpcBaseDocTemplate):
    def __init__(self, out, *args, **kwargs):
        super().__init__(out, *args, **kwargs)
        self.addPageTemplates([
            PageTemplate(id='FirstPage', frames=[self.page_frame], onPage=self.header_cifom)
        ])

    def produce(self):
        self.add_private_data(self.expert)

        data = {
            'student_civility': self.student.civility,
            'student_fullname': self.student.full_name,
            'klass': self.student.klass,
            'date_exam': django_format(self.exam.date_exam, 'j F Y') if self.exam else ''
        }
        self.story.append(Paragraph('<b>Mandat ou autre type d’indemnité</b> (préciser) :', style_normal))
        self.story.append(Paragraph(self.mandat_template.format(**data), style_normal))
        self.story.append(Spacer(0, 0.2 * cm))
        self.story.append(Paragraph(
            '<b>Examen</b>, type d’épreuve et date-s (rédaction, surveillance, correction, travail diplôme, nombre, etc) :',
            style_normal
        ))
        self.story.append(Paragraph(self.examen_template.format(**data), style_normal))

        self.story.append(Spacer(0, 0.2 * cm))

        self.add_accounting_stamp(self.student, self.mandat_type)

        self.build(self.story)


class MentorCompensationPdfForm(CompensationPDFForm):
    mandat_type = CompensationPDFForm.MENTOR_MANDAT
    mandat_template = "Mentoring de {student_civility} {student_fullname}, classe {klass}"
    examen_template = ""
    AMOUNT = ''

    def __init__(self, out, student):
        self.student = student
        self.expert = student.mentor
        self.exam = None
        super().__init__(out)


class EntretienProfCompensationPdfForm(CompensationPDFForm):
    mandat_type = CompensationPDFForm.EXPERT_MANDAT
    mandat_template = "Expert·e aux examens finaux"
    examen_template = (
        "Date des examens : {date_exam}, entretien professionnel de "
        "{student_civility} {student_fullname}, classe {klass}"
    )
    AMOUNT = ''

    def __init__(self, out, exam):
        self.student = exam.student
        self.expert = exam.external_expert
        self.exam = exam
        super().__init__(out)


class SoutenanceCompensationPdfForm(EntretienProfCompensationPdfForm):
    mandat_template = "Expert·e aux examens finaux"
    examen_template = (
        "Date des examens : {date_exam}, soutenance de Travail de diplôme de "
        "{student_civility} {student_fullname}, classe {klass}"
    )
    AMOUNT = ''


class KlassListPDF(EpcBaseDocTemplate):
    """
    Génération des rôles de classes en pdf.
    """
    def __init__(self, out, klass):
        self.klass = klass
        super().__init__(out)

        self.addPageTemplates([
            PageTemplate(id='FirstPage', frames=[self.page_frame], onPage=self.header),
        ])

    def produce(self, klass):

        data = [
            ['Rôle de classe : {0}'.format(klass.name),
             'La Chaux-de-Fonds, le {0}'.format(django_format(date.today(), 'j F Y'))
             ]
        ]
        t = Table(
            data, colWidths=[9 * cm, 9 * cm], rowHeights=(0.4 * cm), hAlign=TA_LEFT, spaceAfter=1 * cm
        )
        t.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (0, 0), 12),
                ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 8),
                ('FONT', (1, 0), (1, 0), 'Helvetica'),
            ]
        ))
        self.story.append(t)

        data = []
        for index, student in enumerate(klass.student_set.all().filter(archived=False).order_by('last_name', 'first_name')):

            data.append(['{0}.'.format(index + 1),
                         '{0} {1}'.format(student.last_name, student.first_name),
                         student.street,
                         student.pcode_city,
                         student.mobile])
            data.append(['', '         Form./Employeur:', student.instructor or ''])
            data.append([''])
            data.append([''])

        t = Table(
            data[0:52], colWidths=[1 * cm, 5 * cm, 5 * cm, 5 * cm, 2 * cm], rowHeights=(0.4 * cm), hAlign=TA_LEFT
        )
        t.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]
        ))
        self.story.append(t)
        if len(data) > 52:
            self.story.append(PageBreak())
            self.story.append(Paragraph("Rôle de classe {0}".format(klass.name), style_bold_title))
            self.story.append(Spacer(0, 2 * cm))

            t = Table(
                data[52:], colWidths=[1 * cm, 5 * cm, 5 * cm, 5 * cm, 2 * cm], rowHeights=(0.4 * cm), hAlign=TA_LEFT
            )
            t.setStyle(TableStyle(
                [
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]
            ))
            self.story.append(t)
        self.build(self.story)
