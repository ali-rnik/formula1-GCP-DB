'use strict';
window.addEventListener('load', function () {
	document.getElementById('sign-out').onclick = function() {
		firebase.auth().signOut();
		window.location.replace('/');

	};

	var uiConfig = {
		signInSuccessUrl: '/',
		signInOptions: [
			firebase.auth.EmailAuthProvider.PROVIDER_ID
		]
	};
	firebase.auth().onAuthStateChanged(function(user) {
		if(user) {
			document.getElementById('sign-out').hidden = false;
			document.getElementById('login-info').hidden = false;
			document.getElementById('add-driver').hidden = false;
			document.getElementById('add-team').hidden = false;
			user.getIdToken().then(function(token) {
				document.cookie = "token=" + token;
			});
		} else {
			var ui = new firebaseui.auth.AuthUI(firebase.auth());
			ui.start('#firebase-auth-container', uiConfig);
			document.getElementById('sign-out').hidden = true;
			document.getElementById('login-info').hidden = true;
			document.getElementById('add-driver').hidden = true;
			document.getElementById('add-team').hidden = true;
			document.cookie = "token=";
		}
	}, function(error) {
		console.log(error);
		alert('Unable to log in: ' + error);
	});
});
