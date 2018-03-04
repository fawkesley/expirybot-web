"use strict";

Element.prototype.addClass = function(className) {
  const el = this;
  if (el.classList)
    el.classList.add(className);
  else
    el.className += ' ' + className;
}

Element.prototype.removeClass = function(className) {
  const el = this;
  if (el.classList)
    el.classList.remove(className);
  else
    el.className = el.className.replace(new RegExp('(^|\\b)' + className.split(' ').join('|') + '(\\b|$)', 'gi'), ' ');
}

String.prototype.contains = function(substring) {
  return this.indexOf(substring) !== -1;
}

function ready(fn) {
  if (document.attachEvent ? document.readyState === "complete" : document.readyState !== "loading"){
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

function setUpPage() {
  hideSubmitButton();
  attachListenerToTextArea();
}

function hideSubmitButton() {
  const button = document.getElementById('submit-button');
  button.addClass('hidden');
}

function attachListenerToTextArea() {
  const textarea = document.getElementById('id_public_key');
  console.log(textarea);

  textarea.addEventListener('input', handleTextAreaChange);
}

function handleTextAreaChange(event) {
  const textarea = document.getElementById('id_public_key'),
        content = textarea.value.trim();

  const PRIVATE_KEY_HEADER = '-----BEGIN PGP PRIVATE KEY BLOCK-----',
        PUBLIC_KEY_HEADER = '-----BEGIN PGP PUBLIC KEY BLOCK-----',
        PUBLIC_KEY_FOOTER = '-----END PGP PUBLIC KEY BLOCK-----';

  if(content.contains(PRIVATE_KEY_HEADER)) {

    warnAboutPrivateKey();

  } else if(content.startsWith(PUBLIC_KEY_HEADER) && content.endsWith(PUBLIC_KEY_FOOTER)) {

    clearWarnings();
    uploadPublicKey(content);

  } else {
    warnAboutFormat();
  }

}

function uploadPublicKey(public_key) {
  const textarea = document.getElementById('id_public_key');
  const form = document.getElementById('public-key-form');

  fillProgressBar();

  window.setTimeout(function() {
    form.submit();
  }, 1500);

}

function fillProgressBar() {
  const progressWrapper = document.getElementById('progress-wrapper');
  const progressBar = document.getElementById('progress-bar');

  progressWrapper.removeClass('hidden');

  var currentValue = 0;

  var tick = function() {
    currentValue += 10;
    progressBar.setAttribute('aria-valuenow', currentValue);
    progressBar.setAttribute('style', `width: ${currentValue}%;`);


    if(currentValue < 100) {
      window.setTimeout(tick, 50);
    }

  }

  window.setTimeout(tick, 50);
}

function clearWarnings() {

  const form_group = document.getElementById('public-key-form-group'),
        help_blocks = document.getElementsByClassName('help-block');

  form_group.removeClass('has-warning');
  form_group.removeClass('has-error');

  for(var i=0 ; i < help_blocks.length ; ++i) {
    help_blocks[i].addClass('hidden');
  }
}

function warnAboutFormat() {
  const form_group = document.getElementById('public-key-form-group');
  const textarea = document.getElementById('id_public_key');
  const format_warning = document.getElementById('format-warning');

  form_group.addClass('has-warning');
  format_warning.removeClass('hidden');
}

function warnAboutPrivateKey() {
  const form_group = document.getElementById('public-key-form-group');
  const textarea = document.getElementById('id_public_key');
  const private_key_warning = document.getElementById('private-key-warning');

  form_group.addClass('has-error');
  private_key_warning.removeClass('hidden');
  textarea.setAttribute('disabled', '');
}


ready(setUpPage);
