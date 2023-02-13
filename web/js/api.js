const apiBaseURL = "https://cv.artbred.io"

function getUTMString() {
    const queryParams = new URLSearchParams(window.location.search)
    const utmRegex = new RegExp("^utm_")

    let utmArray = []
   
    for (const [key, value] of queryParams) {
        if (utmRegex.test(key)) {
            utmArray.push(`${key}=${value}`)
        }
    }

    return utmArray.join("&");
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

async function getCV(token) {
    let getCvResponse = await fetch(`${apiBaseURL}/download?${getUTMString()}`, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'token': token})
    })

    if (!getCvResponse?.ok) {
        let body = await getCvResponse.json()
        alert(body.detail)
        return
    }

    const fileBlob = await getCvResponse.blob()
    downloadBlob(fileBlob, "artbred.io.pdf")
}

async function scorePosition() {
    let position_input = document.getElementById('position-input').value
    let postion_len = position_input.length

    if (postion_len < 5) {
        alert("Please enter at least 5 characters")
        return
    }

    if (postion_len > 50) {
        alert("The text is too long, reduce it to 50 characters")
        return
    }

    try {
        let scoreResponse = await fetch(`${apiBaseURL}/score?${getUTMString()}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'position': position_input})
        })

        let body = await scoreResponse.json()

        if (!scoreResponse?.ok) {
            alert(body.detail)
            return
        }

        if (confirm(body.detail)) {
            await getCV(body.token)
        }

    } catch (error) {
        console.error(error)
        alert('Please try again later')
        return
    }

}