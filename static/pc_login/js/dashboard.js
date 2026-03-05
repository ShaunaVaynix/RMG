const cols = 20, rows = 12;
let tiles = Array(cols * rows).fill("empty");
let isDragging = false;
let selectedPC = "vip";
let selectedUtil = null;

// ===== BORDER WALLS =====
function initializeWalls(){
    for(let x=0;x<cols;x++){
        tiles[x] = "wall";
        tiles[(rows-1)*cols+x] = "wall";
    }
    for(let y=0;y<rows;y++){
        tiles[y*cols] = "wall";
        tiles[y*cols+cols-1] = "wall";
    }
}

// ===== LOAD FROM DATABASE =====
function loadExistingPCs(){
    fetch("/api/get_computers_json/")
    .then(res=>res.json())
    .then(data=>{
        tiles = Array(cols * rows).fill("empty");
        initializeWalls();

        for(let room in data){
            data[room].forEach(pc=>{
                if(pc.position !== null && pc.position < tiles.length){
                    tiles[pc.position] = {
                        type: pc.room.toLowerCase(),
                        label: pc.pc_id
                    };
                }
            });
        }

        render();
        updateDashboard();
    })
    .catch(err=>console.error(err));
}

// ===== RENDER GRID =====
function render(){
    const grid = document.getElementById("grid");
    grid.innerHTML = "";

    tiles.forEach((tile,i)=>{
        const div = document.createElement("div");

        if(typeof tile === "object"){
            div.className = "tile " + tile.type;
            div.innerText = tile.label;
        }else{
            div.className = "tile " + tile;
        }

        div.addEventListener("mousedown",()=>{
            applyTile(i);
            isDragging=true;
        });

        div.addEventListener("mouseenter",()=>{
            if(isDragging) applyTile(i);
        });

        div.addEventListener("mouseup",()=> isDragging=false);

        grid.appendChild(div);
    });
}

document.addEventListener("mouseup",()=> isDragging=false);

// ===== UPDATE DASHBOARD CARDS =====
function updateDashboard(){
    const total = tiles.filter(t=> typeof t==="object").length;
    document.getElementById("total").innerText = total;
    document.getElementById("available").innerText = total;
}

// ===== APPLY TILE =====
function applyTile(i){
    if(selectedPC && tiles[i] !== "wall" && typeof tiles[i] !== "object"){
        const label = generateLabel(selectedPC);

        tiles[i] = {
            type: selectedPC,
            label: label
        };

        saveTileToBackend(i, tiles[i]);
    }
    else if(selectedUtil){
        if(selectedUtil==="delete"){
            removeTileBackend(i);
        }
        else if(tiles[i] !== "wall"){
            tiles[i] = selectedUtil;
            render();
        }
    }
}

// ===== GENERATE LABEL =====
function generateLabel(type){
    const count = tiles.filter(t=> typeof t==="object" && t.type===type).length + 1;
    return type.charAt(0).toUpperCase() + count;
}

// ===== SAVE TO BACKEND =====
function saveTileToBackend(i,tile){
    fetch("/api/add_computer/",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "X-CSRFToken":getCSRFToken()
        },
        body:JSON.stringify({
            pc_id: tile.label,
            type: tile.type,
            specs:"Intel i7 | 32GB RAM | RTX3080",
            status:"Available",
            position:i
        })
    })
    .then(res=>res.json())
    .then(resp=>{
        if(resp.error){
            alert(resp.error);
            loadExistingPCs();
        }else{
            loadExistingPCs();
        }
    })
    .catch(err=>console.error(err));
}

// ===== DELETE =====
function removeTileBackend(i){
    if(typeof tiles[i] !== "object"){
        tiles[i] = "empty";
        render();
        return;
    }

    const pc_id = tiles[i].label;

    fetch(`/api/delete_computer/${pc_id}/`,{
        method:"DELETE",
        headers:{ "X-CSRFToken":getCSRFToken() }
    })
    .then(res=>res.json())
    .then(()=>{
        loadExistingPCs();
    })
    .catch(err=>console.error(err));
}

// ===== CSRF =====
function getCSRFToken(){
    const cookies=document.cookie.split(';');
    for(let cookie of cookies){
        cookie=cookie.trim();
        if(cookie.startsWith("csrftoken="))
            return decodeURIComponent(cookie.substring("csrftoken=".length));
    }
    return null;
}

// ===== START =====
initializeWalls();
loadExistingPCs();
setInterval(loadExistingPCs,5000);