function sizegdiff(img, fac) {
	let w = img.naturalWidth
	let h = img.naturalHeight
	let div = img.parentElement
	// window.confirm("width: " + w + " height: " + h)
	div.style.width = Math.ceil(fac * w / {{ adjust[0] }}) + "px"
	div.style.height = Math.ceil(fac * h / {{ adjust[1] }}) + "px"
}

function sizeOnLoad(img, fac) {
	if (img.complete) {
		sizegdiff(img, fac)
	} else {
		img.onload = function() { sizegdiff(img, fac) }
	}
}

function chmag(value) {
	let matches = document.querySelectorAll(".glinfo img")
	matches.forEach(function(img) { sizeOnLoad(img, value) })
}

up.compiler('.glinfo img', function(img) { sizeOnLoad(img, {{ mag }}) })
up.compiler('#mainlist .gdiff img', function(img) { sizeOnLoad(img, {{ diffmag }}) })

