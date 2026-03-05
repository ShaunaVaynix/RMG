function refreshComputers() {
    fetch("/api/get_computers_json/")
        .then(res => res.json())
        .then(data => {
            for (let room in data) {
                const container = document.getElementById(room.toLowerCase()+"Room");
                if(!container) continue;
                container.innerHTML="";
                data[room].forEach(pc=>{
                    const card = document.createElement("div");
                    card.className="pc-card";
                    card.innerHTML = `<h5>${pc.pc_id}</h5>
                                      <p>${pc.specs}</p>
                                      <span class="status-badge status-${pc.status.replace(/\s+/g,'')}">${pc.status}</span>`;
                    container.appendChild(card);
                });
            }
        }).catch(err=>console.error(err));
}

// Auto-refresh every 5s
setInterval(refreshComputers,5000);
refreshComputers();