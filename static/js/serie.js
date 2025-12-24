const encodePath = (value) =>
    value
        .replace(/\\/g, "/")
        .split("/")
        .map((segment) => encodeURIComponent(segment))
        .join("/");

document.addEventListener("DOMContentLoaded", () => {
    const episodesList = document.getElementById("episodesList");
    const seasonSelect = document.getElementById("seasonSelect");

    if (!episodesList || !seasonSelect) {
        return;
    }

    const serieName = episodesList.dataset.serie || "";
    const watchBase = episodesList.dataset.watchBase || "";

    const buildEpisodeCard = (episode, index) => {
        const item = document.createElement("article");
        item.className = "episode-item";
        item.style.setProperty("--delay", `${index * 60}ms`);

        const thumbWrapper = document.createElement("div");
        thumbWrapper.className = "episode-thumb-wrapper skeleton";

        const thumb = document.createElement("img");
        thumb.className = "episode-thumb";
        thumb.src = episode.thumb;
        thumb.alt = `Thumb do episódio ${episode.number}`;
        thumb.loading = "lazy";
        thumb.decoding = "async";

        const markLoaded = () => {
            thumb.classList.add("loaded");
            thumbWrapper.classList.add("loaded");
        };

        if (thumb.complete) {
            markLoaded();
        } else {
            thumb.addEventListener("load", markLoaded);
        }

        thumbWrapper.appendChild(thumb);

        const content = document.createElement("div");
        content.className = "episode-content";

        const number = document.createElement("p");
        number.className = "episode-number";
        number.textContent = `Episódio ${episode.number}`;

        const title = document.createElement("h3");
        title.className = "episode-title";
        title.textContent = episode.filename;

        const description = document.createElement("p");
        description.className = "episode-description";
        description.textContent = episode.description;

        const action = document.createElement("a");
        action.className = "btn btn-primary";
        action.textContent = "Assistir";
        action.href = watchBase.replace("__PATH__", encodePath(episode.relative_path));

        content.appendChild(number);
        content.appendChild(title);
        content.appendChild(description);
        content.appendChild(action);

        item.appendChild(thumbWrapper);
        item.appendChild(content);

        return item;
    };

    const loadSeason = async (seasonIndex) => {
        episodesList.innerHTML = "";
        episodesList.classList.add("is-loading");

        try {
            const response = await fetch(
                `/api/serie/${encodeURIComponent(serieName)}/temporada/${seasonIndex}`
            );
            const data = await response.json();
            const episodes = data.episodes || [];

            if (!episodes.length) {
                const empty = document.createElement("div");
                empty.className = "empty-state";
                empty.innerHTML = "<h2>Sem episódios</h2><p>Não encontramos episódios nessa temporada.</p>";
                episodesList.appendChild(empty);
                return;
            }

            episodes.forEach((episode, index) => {
                episodesList.appendChild(buildEpisodeCard(episode, index));
            });
        } catch (error) {
            const empty = document.createElement("div");
            empty.className = "empty-state";
            empty.innerHTML = "<h2>Algo deu errado</h2><p>Não conseguimos carregar os episódios agora.</p>";
            episodesList.appendChild(empty);
        } finally {
            episodesList.classList.remove("is-loading");
        }
    };

    seasonSelect.addEventListener("change", (event) => {
        loadSeason(event.target.value);
    });

    loadSeason(0);
});
