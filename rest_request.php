<?php
// Point to where you downloaded the phar
include('./httpful.phar');

// And you're ready to go!
$response = \Httpful\Request::get('http://127.0.0.1:5000')->send();
?>
