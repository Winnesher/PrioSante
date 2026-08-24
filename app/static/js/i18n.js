(function () {
    var STORAGE_KEY = 'priosante-lang';

    var translations = {
        en: {
            // base.html — navbar & footer
            'nav.home': 'Home',
            'nav.register': 'Patient Registration',
            'nav.appointment': 'My Appointment',
            'nav.dashboard': 'Dashboard',
            'nav.logout': 'Log Out',
            'nav.staffArea': 'Staff Area',
            'footer.copyright': 'PrioSanté, University of Lomé. Hospital demonstration prototype. All rights reserved.',
            'footer.team': 'Team',

            // landing.html — hero
            'landing.hero.badge': 'Academic Prototype, University of Lomé',
            'landing.hero.title': "No more waiting blindly at the hospital.",
            'landing.hero.desc': '<strong>PrioSanté</strong> reinvents hospital reception: remote registration, automatic clinical priority scoring from symptoms, and smart 15-minute slot allocation.',
            'landing.hero.stat1': 'Optimized slots',
            'landing.hero.stat2': 'Automatic triage',
            'landing.hero.stat3': 'Delay before emergency',

            // landing.html — "Pourquoi PrioSanté"
            'landing.why.title': 'Why PrioSanté transforms patient reception',
            'landing.why.subtitle': 'A system designed for patient comfort and care team efficiency.',
            'landing.why.card1.title': 'Automated Clinical Triage',
            'landing.why.card1.desc': 'The patient answers closed questions about their symptoms. The algorithm computes a score from 0 to >12 and assigns the right priority (Low, Medium, High, Emergency).',
            'landing.why.card2.title': 'Fixed 15-Minute Slots',
            'landing.why.card2.desc': 'No more mass crowding at 7am! Each patient gets a precise time slot, optimized according to their urgency level.',
            'landing.why.card3.title': 'Life-Threatening Emergency Detection',
            'landing.why.card3.desc': 'For severe symptoms (score > 12), no regular slot is assigned: the system triggers an immediate redirection to physical emergency care.',
            'landing.why.card4.title': 'Strict Confidentiality',
            'landing.why.card4.desc': "Reception staff see arrivals and delays without access to symptoms. The doctor has the full clinical record.",
            'landing.why.card5.title': 'SMS Reminders & Delay Management',
            'landing.why.card5.desc': 'Simulated confirmation notifications. If a patient is more than 10 minutes late, they are automatically moved to the end of the queue.',
            'landing.why.card6.title': 'Real-Time Staff Dashboard',
            'landing.why.card6.desc': 'Interactive dashboard to log arrivals, call patients in, and close consultations in one click.',

            // landing.html — "Comment ça marche"
            'landing.how.title': 'How does it work?',
            'landing.how.subtitle': 'A journey designed for both patients and care staff.',
            'landing.how.step1.eyebrow': 'Step 1: Patient',
            'landing.how.step1.title': 'A simple registration, wherever you are',
            'landing.how.step1.desc': 'From your phone, enter your details and answer a 3-step symptom questionnaire. PrioSanté computes your clinical score and immediately offers a 15-minute slot matched to your priority.',
            'landing.how.step1.cta': 'Register & Get My Slot',
            'landing.how.step2.eyebrow': 'Step 2: Care Staff',
            'landing.how.step2.title': 'Real-time management for teams',
            'landing.how.step2.desc': 'Receptionists and doctors each have their own dashboard: queue sorted by priority, arrival and delay management, one-click status updates.',
            'landing.how.step3.eyebrow': 'Step 3: Consultation Day',
            'landing.how.step3.title': 'Seen at the exact scheduled time',
            'landing.how.step3.desc': "On the day, you're welcomed at the exact time of your slot and seen by a doctor who already has your complete clinical file.",

            // landing.html — roadmap
            'landing.roadmap.title': 'An ambition beyond the prototype',
            'landing.roadmap.subtitle': 'PrioSanté is designed from the start to grow into a large-scale hospital platform. Here are the next steps.',
            'landing.roadmap.item1.title': 'Real SMS / USSD Gateway (Kannel/Gammu)',
            'landing.roadmap.item1.desc': 'Allow patients with a basic phone (no internet) to register by dialing a USSD code (e.g. `*360#`).',
            'landing.roadmap.item2.title': 'Multi-Hospital & Multi-Specialty',
            'landing.roadmap.item2.desc': 'Rollout to pediatrics, gynecology, cardiology, and interconnection between several partner health centers.',
            'landing.roadmap.item3.title': 'AI Assistant & Predictive Triage',
            'landing.roadmap.item3.desc': "Integration of an AI-assisted clinical decision model to refine scoring based on the patient's vital signs.",
            'landing.roadmap.item4.title': 'Monitoring & Data Analytics (Grafana)',
            'landing.roadmap.item4.desc': 'Analytics dashboards for hospital management: attendance peaks, average wait time per department.',
            'landing.roadmap.item5.title': 'On-Duty Pharmacy Network',
            'landing.roadmap.item5.desc': 'Real-time location of nearby on-duty pharmacies, with hours and availability, directly accessible from the patient account.',

            // landing.html — team
            'landing.team.title': 'Our Team',
            'landing.team.role1': 'Physics Student, Physics Teacher',
            'landing.team.role2': 'Physics Student, CanalBox Installation Technician',
            'landing.team.role3': 'Physics Student, specializing in DevOps, AI, MLOps',

            // landing.html — contact
            'landing.contact.title': 'Contact Us',
            'landing.contact.tagline': 'A question? Get in touch',
            'landing.contact.desc': 'Our team is available to answer your questions about the PrioSanté project.',
            'landing.contact.phoneLabel': 'Phone',

            // inscription.html
            'inscription.title': 'Book Your Appointment Online',
            'inscription.subtitle': 'Fill in the form below to automatically get an optimized time slot based on your condition.',
            'inscription.step1.tab': 'Your Details',
            'inscription.step2.tab': 'Service Selection',
            'inscription.step3.tab': 'Symptom Questionnaire',
            'inscription.step1.heading': 'Step 1: Personal Information',
            'inscription.field.lastName': 'Last Name *',
            'inscription.field.lastNamePh': 'e.g. KOGNON',
            'inscription.field.firstName': 'First Name *',
            'inscription.field.firstNamePh': 'e.g. Romeo',
            'inscription.field.phone': 'Phone Number (SMS) *',
            'inscription.field.phonePh': '90 12 34 56',
            'inscription.field.dob': 'Date of Birth *',
            'inscription.field.gender': 'Gender',
            'inscription.field.genderM': 'Male',
            'inscription.field.genderF': 'Female',
            'inscription.field.genderOther': 'Other / Prefer not to say',
            'inscription.step1.next': 'Next: Choose Service ➔',
            'inscription.step2.heading': 'Step 2: Medical Service Selection',
            'inscription.step2.label': 'Choose the relevant specialty or department *',
            'inscription.step2.duration': 'Average consultation time',
            'inscription.btn.previous': 'Previous',
            'inscription.step2.next': 'Next: Symptoms ➔',
            'inscription.step3.heading': 'Step 3: Symptom Assessment',
            'inscription.step3.instructions': 'Check all boxes matching the symptoms you or the patient are currently experiencing.',
            'inscription.step3.points': 'Points',
            'inscription.step3.scoreLabel': 'Indicative score:',
            'inscription.step3.urgenceAlert': 'Warning: high score, a redirection to emergency care will be required.',
            'inscription.step3.submit': 'Confirm & Get Appointment Time',
            'inscription.modal.ok': 'Got it',
            'inscription.js.needSymptom': 'Please check at least one symptom before submitting your request.',
            'inscription.js.fillFields': 'Please fill in your Last Name, First Name, Phone Number and Date of Birth before continuing.',
            'inscription.js.lettersOnly': 'Last Name and First Name must only contain letters.',
            'inscription.js.invalidDobTodayOrFuture': "Today's date (present date) and future dates cannot be used as date of birth. Please select a valid past date of birth.",
            'inscription.js.invalidDobTooOld': 'The date of birth is too far in the past (over 120 years ago). Please select a valid date of birth.',
            'inscription.js.invalidDob': 'Please select a valid date of birth before continuing.',

            // confirmation.html
            'confirmation.title': 'Your Appointment is Confirmed',
            'confirmation.thanksPrefix': 'Thank you Mr. / Mrs.',
            'confirmation.thanksSuffix': 'Your request has been successfully processed by the PrioSanté allocation engine.',
            'confirmation.pass.eyebrow': 'PrioSanté: Consultation Pass',
            'confirmation.pass.title': 'Appointment Confirmed',
            'confirmation.pass.time': 'Time',
            'confirmation.pass.service': 'Service',
            'confirmation.pass.date': 'Date',
            'confirmation.pass.codeLabel': 'Code to present at reception',
            'confirmation.downloadBtn': 'Download my consultation pass',
            'confirmation.smsHeader': 'Simulated SMS / USSD sent to',
            'confirmation.btnAnother': 'Book Another Appointment',
            'confirmation.btnTrack': 'Track My Appointment Status ➔',
            'confirmation.pdf.subtitle': 'Appointment Confirmed: Consultation Pass',
            'confirmation.pdf.time': 'TIME',
            'confirmation.pdf.service': 'SERVICE',
            'confirmation.pdf.date': 'DATE',
            'confirmation.pdf.codeLabel': 'CODE TO PRESENT AT RECEPTION',

            // urgence.html
            'urgence.badge': 'Medical Emergency',
            'urgence.title': 'Immediate Redirection to Emergency Care',
            'urgence.noSlot': 'No regular time slot has been assigned to you.',
            'urgence.instructions': 'Given the severity of your declared symptoms, you must go immediately to the nearest physical emergency department or call emergency services.',
            'urgence.patientName': 'Patient Name',
            'urgence.code': 'Emergency Code',
            'urgence.smsHeader': 'Simulated SMS / USSD alert sent to',
            'urgence.sms.prefix': 'PrioSanté ALERT: Mr. / Mrs.',
            'urgence.sms.suffix': 'following your critical symptoms, please go IMMEDIATELY to the hospital emergency department.',
            'urgence.btnHome': 'Back to Home',
            'urgence.btnCall': 'Call Emergency Services',
            'urgence.callModalTitle': 'Call Emergency Services',
            'urgence.callModalSub': 'Please select your preferred emergency calling option:',
            'urgence.opt1.title': '1) General Emergency',
            'urgence.opt1.desc': 'National general emergency services (SAMU, rescue and medical assistance).',
            'urgence.opt1.btn': 'Call (8200)',
            'urgence.opt2.title': '2) Hospital Emergency',
            'urgence.opt2.desc': 'Direct internal emergency line for this hospital.',
            'urgence.opt2.btn': 'Call (90922358)',

            // mon_rdv.html
            'rdv.title': 'Track Your Appointment',
            'rdv.subtitle': 'Enter your phone number or your booking code (e.g. PS-A9F32).',
            'rdv.searchPh': 'Appointment Code (e.g. PS-12345) or Phone Number...',
            'rdv.searchBtn': 'Search',
            'rdv.codeLabel': 'Code',
            'rdv.expectedTime': 'Expected Time:',
            'rdv.priorityLevel': 'Priority Level:',
            'rdv.service': 'Service',
            'rdv.date': 'Date',
            'rdv.notFound': 'No booking found for this search. Check your input or register again.',
            'rdv.missedTitle': 'You missed this appointment',
            'rdv.missedDesc': 'Reception marked you as absent and your slot has been freed up. Please submit a new consultation request to get a new time slot.',
            'rdv.missedCta': 'Make a new request',

            // status pills (shared)
            'status.enAttente': 'Waiting',
            'status.arrive': 'Arrived at Hospital',
            'status.enConsultation': 'In Consultation',
            'status.termine': 'Consultation Completed',
            'status.enRetard': 'Delayed',
            'status.absent': 'Absent',
            'status.serviceOuvert': 'Service open',
            'status.serviceFerme': 'Service closed',

            // priority badges (shared)
            'badge.faible': 'Low',
            'badge.moyenne': 'Medium',
            'badge.elevee': 'High',
            'badge.urgence': 'Emergency',
            'status.arriveShort': 'Arrived',
            'status.termineShort': 'Completed',

            // login.html
            'login.title': 'Hospital Staff Area',
            'login.subtitle': 'Secure access for Receptionist or Doctor accounts.',
            'login.username': 'Username',
            'login.usernamePh': 'Your username',
            'login.password': 'Password',
            'login.submit': 'Log In to Dashboard',

            // dashboard_reception.html
            'reception.title': 'Reception Dashboard',
            'reception.subtitle': 'Arrival management, daily queue & delay tracking (Logged in as',
            'reception.role': 'Role: Receptionist',
            'reception.stat.total': "Registered Today",
            'reception.stat.arrived': 'Arrived at Hospital',
            'reception.stat.emergencies': 'Emergency Redirections',
            'reception.queueTitle': 'Live General Medicine Queue',
            'reception.th.codeTime': 'Code / Time',
            'reception.th.name': 'Full Name',
            'reception.th.phone': 'Phone',
            'reception.th.priority': 'Priority',
            'reception.th.status': 'Status',
            'reception.th.actions': 'Reception Actions',
            'reception.confirmDelay': 'Report a delay (+15 min) for this patient?',
            'reception.delayBtn': 'Delayed >10m',
            'reception.confirmAbsent': 'Mark this patient as absent? Their slot will be freed up.',
            'reception.absentBtn': 'Absent',
            'reception.modal.cancel': 'Cancel',
            'reception.modal.confirm': 'Confirm',
            'reception.overdue': 'Slot overdue',
            'reception.inWaitingRoom': 'In waiting room',
            'reception.noConsultations': 'No consultations recorded for today.',

            // dashboard_medecin.html
            'medecin.title': 'Medical Consultation Dashboard',
            'medecin.subtitle': 'Full clinical view: declared symptoms, scores & triage (Dr.',
            'medecin.role': 'Role: Practicing Doctor',
            'medecin.stat.total': "Today's Consultations",
            'medecin.stat.inProgress': 'In Progress',
            'medecin.stat.done': 'Completed',
            'medecin.queueTitle': 'Clinical Queue (Sorted by Urgency & Time)',
            'medecin.th.timeCode': 'Time / Code',
            'medecin.th.patient': 'Patient',
            'medecin.th.scorePriority': 'Score / Priority',
            'medecin.th.symptoms': 'Declared Symptoms',
            'medecin.th.action': 'Medical Action',
            'medecin.tel': 'Tel',
            'medecin.criticalEmergency': 'Critical Emergency',
            'medecin.noSymptoms': 'No symptoms reported',
            'medecin.callPatient': 'Call Patient',
            'medecin.endConsultation': 'End Consultation',
            'medecin.closed': 'Consultation Closed',
            'medecin.noPatients': 'No patients in the queue today.'
        }
    };

    function setCache(el, attr, cacheAttr, current) {
        if (!el.hasAttribute(cacheAttr)) {
            el.setAttribute(cacheAttr, current);
        }
    }

    function applyLanguage(lang) {
        var isEn = lang === 'en';
        document.documentElement.setAttribute('lang', isEn ? 'en' : 'fr');

        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            var key = el.getAttribute('data-i18n');
            setCache(el, 'text', 'data-fr-cache', el.textContent);
            var frText = el.getAttribute('data-fr-cache');
            el.textContent = (isEn && translations.en[key]) ? translations.en[key] : frText;
        });

        document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-html');
            setCache(el, 'html', 'data-fr-cache-html', el.innerHTML);
            var frHtml = el.getAttribute('data-fr-cache-html');
            el.innerHTML = (isEn && translations.en[key]) ? translations.en[key] : frHtml;
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-placeholder');
            setCache(el, 'placeholder', 'data-fr-cache-ph', el.getAttribute('placeholder') || '');
            var frText = el.getAttribute('data-fr-cache-ph');
            el.setAttribute('placeholder', (isEn && translations.en[key]) ? translations.en[key] : frText);
        });

        document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-title');
            setCache(el, 'title', 'data-fr-cache-title', el.getAttribute('title') || '');
            var frText = el.getAttribute('data-fr-cache-title');
            el.setAttribute('title', (isEn && translations.en[key]) ? translations.en[key] : frText);
        });

        var labels = document.querySelectorAll('.lang-toggle-label');
        labels.forEach(function (el) {
            el.textContent = isEn ? 'EN' : 'FR';
        });
    }

    function currentLang() {
        return localStorage.getItem(STORAGE_KEY) || 'fr';
    }

    function toggleLang() {
        var next = currentLang() === 'fr' ? 'en' : 'fr';
        localStorage.setItem(STORAGE_KEY, next);
        applyLanguage(next);
    }

    function t(key, frFallback) {
        return (currentLang() === 'en' && translations.en[key]) ? translations.en[key] : frFallback;
    }

    window.PrioSanteI18n = {
        translations: translations,
        applyLanguage: applyLanguage,
        currentLang: currentLang,
        t: t
    };

    document.addEventListener('DOMContentLoaded', function () {
        applyLanguage(currentLang());
        var toggle = document.getElementById('langToggle');
        if (toggle) {
            toggle.addEventListener('click', toggleLang);
        }
    });
})();
