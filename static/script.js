function createVideoElement(camera, thumbnail = false) {
    const element = document.createElement("img");
    element.classList.add("video-feed");
    element.dataset.camera = camera;
    element.src = VIDEO_FEED_BASE + `?camera=${camera}&thumbnail=${thumbnail}`;
    return element;
}

function getCamerasElement(camerasElementSubElement) {
    let camerasElement = camerasElementSubElement.parentElement;
    while (camerasElement && !camerasElement.classList.contains("cameras")) {
        camerasElement = camerasElement.parentElement;
    }
    return camerasElement;
}

function getMainView(camerasElementSubElement) {
    const camerasElement = getCamerasElement(camerasElementSubElement);
    return camerasElement.querySelector(".main-view");
}

document.querySelectorAll(".video-feed").forEach((videoFeedElement) => {
    videoFeedElement.addEventListener("click", () => {
        const mainViewElement = getMainView(videoFeedElement);
        while (mainViewElement.firstChild) {
            mainViewElement.removeChild(mainViewElement.lastChild);
        }

        videoFeedElement.parentElement.querySelectorAll(".video-feed").forEach((element) => {
            element.classList.remove("selected");
        });
        videoFeedElement.classList.add("selected");

        const camera = videoFeedElement.dataset.camera;
        mainViewElement.appendChild(createVideoElement(camera))
    });
});