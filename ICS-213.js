var EOL = '%0A';
var SEPARATOR = '--------------------';
var ALL = false;	/* include all fields even if empty */

function aName(a, b) {
	/* adds field name : value to the body string,
			but only if field isn't empty */
	try {
		var bb = document.getElementsByName(b)[0].value;
		if (ALL || bb.length) {
			return a + b + ': '+ bb + EOL;
		}
		else {
			return a;
		}
	}
	catch {
		return a;
	}
}

function aChk(a, b) {
	try {
		var chk = document.getElementsByName(b)[0].checked;
		if (chk) {
			return a + b + ': X' + EOL;
		}
		else {
			if (ALL) {
				return a + b + ': ' + EOL;
			}
			else {
				return a;
			}
		}
	}
	catch {
		return a;
	}
}

function aStr(a, b) {
	return a + b + EOL;
}

function anyInputs(list) {
	var ll = list.length;
	for (var i=0; i<ll; i++) {
		try {
			if (document.getElementsByName(list[i])[0].value.length) {
				return true;
			}
		}
		finally {
		}
	}
	return false;
}

function makePacket() {
	try {
		var pto = document.getElementsByName('PACKET_TO')[0].value;
		var act = document.getElementById('FORM_213').action;
		var m = '';
		var r = '';
		var subject = '';
		var body = '';
		var err = '';

		if (pto.length == 0) {
			err = err + "'Packet message to' is highly recommended. ";
		}

		/* build subject */
		try {
			subject = document.getElementsByName('SUBJECT')[0].value;
			subject = subject.trim();
		}
		catch {
		}
		if (subject.length == 0) {
			err = err + "'Subject' is recommended. ";
		}

		/* build body */
		body = aName(body, 'TO');
		body = aName(body, 'TO_LOCATION');
		body = aName(body, 'FROM');
		body = aName(body, 'FROM_LOCATION');

		body = aStr (body, SEPARATOR);
		body = aStr (body, '(213A)');
		body = aName(body, 'SUBJECT');
		body = aName(body, 'ORIGINAL_OR_REPLY');
		body = aChk (body, 'FIRE_OR_HAZMAT');
		body = aChk (body, 'MEDICAL');
		body = aChk (body, 'RESCUE');
		body = aChk (body, 'INFRASTRUCTURE');
		body = aChk (body, 'OTHER');
		body = aName(body, 'INCIDENT_ADDRESS');
		body = aName(body, 'CROSS_STREET');

		body = aStr (body, SEPARATOR);
		body = aName(body, 'DATE');
		body = aName(body, 'TIME');
		body = aName(body, 'MSG_NUMBER');
		body = aName(body, 'PRIORITY');
		body = aName(body, 'REPLY_REQUIRED');

		if (ALL || anyInputs(['MESSAGE', 'SIGNATURE', 'POSITION', 'SENT_RECD_DT', 'CALLSIGN', 'TACTICAL'])) {
			body = aStr (body, SEPARATOR);
			body = aStr (body, 'MESSAGE:');
			/* the message needs LF replaced by %0A */
			m = document.getElementsByName('MESSAGE')[0].value.replace(/\n/g, '%0A');
			body = aStr (body, m);
			if (m.length > 1000) {
				err = err + "This message is rather long for packet radio. ";
			}

			if (ALL || anyInputs(['SIGNATURE', 'POSITION', 'SENT_RECD_DT', 'CALLSIGN', 'TACTICAL'])) {
				body = aStr (body, SEPARATOR);
				body = aName(body, 'SIGNATURE');
				body = aName(body, 'POSITION');
				body = aName(body, 'SENT_RECD_DT');
				body = aName(body, 'CALLSIGN');
				body = aName(body, 'TACTICAL');
			}
		}

		if (ALL || anyInputs(['REPLY', 'REF_MSG_NUMBER', 'REPLY_SIGNATURE', 'REPLY_POSITION', 'REPLY_DT', 'REPLY_CALLSIGN', 'REPLY_TACTICAL'])) {
			body = aStr (body, SEPARATOR);
			body = aName(body, 'REF_MSG_NUMBER');
			body = aStr (body, 'REPLY:');

			/* the message needs LF replaced by %0A */
			var r = document.getElementsByName('REPLY')[0].value.replace(/\n/g, '%0A');
			body = aStr (body, r);

			if (ALL || anyInputs(['REPLY_SIGNATURE', 'REPLY_POSITION', 'REPLY_DT', 'REPLY_CALLSIGN', 'REPLY_TACTICAL'])) {
				body = aStr (body, SEPARATOR);
				body = aName(body, 'REPLY_SIGNATURE');
				body = aName(body, 'REPLY_POSITION');
				body = aName(body, 'REPLY_DT');
				body = aName(body, 'REPLY_CALLSIGN');
				body = aName(body, 'REPLY_TACTICAL');
			}
		}

		if (m.length == 0 && r.length == 0) {
			err = err + "\n\nYou did not include a message or a reply! ";
		}

		body = aStr (body, SEPARATOR);

		document.getElementById('FORM_213').action = 'mailto:<'+pto+'>?subject='+subject+'&body='+body;
		if (err.length) {
			err = err + '\n\nChoose \'Cancel\' to go back and fix this, or \'OK\' to open your mail program and continue.';
			return confirm(err);
		}
		return true;
	}
	catch (err) {
		alert(err.message);
		return false;
	}
}
