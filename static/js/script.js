function cardColor(card){
    if(card.dataset.suit === "S" || card.dataset.suit === "C")
        return "Black";
    return "Red"
}
function cardRank(card){
    switch(card.dataset.rank){
        case "A": return "1";
        case "T": return "10";
        case "J": return "11";
        case "Q": return "12";
        case "K": return "13";
        default: return card.dataset.rank;
    }
}
function canStack(FrontCard,BackCard){
    if(+cardRank(FrontCard) != +cardRank(BackCard) - 1 || cardColor(FrontCard) === cardColor(BackCard))
        return false;
    return true;
}
function isValidStack(stack){
    let parent = [...stack.parentElement.children];
    let index = parent.indexOf(stack);
    for(let i = index + 1; i < parent.length; i++){
        if(!canStack(parent[i],parent[i-1]))
            return false;
    }
    return parent.slice(index);
}


let stack = null;
let offsetX,offsetY
document.addEventListener("mousedown", (e) => {

    //Detect stack
    const element = document.elementFromPoint(e.clientX, e.clientY).closest(".card");
    stack = isValidStack(element);
    if(element.classList.contains("card") && stack){ 
        for(card in stack){
            stack[card].style.pointerEvents = "none";
            stack[card].style.zIndex = 1000;
        }
    } 
    const rect = stack[0].getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
}); 

document.addEventListener("mousemove", (e) => {
    //Đang di chuyển stack
    if(stack){
        const parent_rect = stack[0].parentElement.getBoundingClientRect();

        for(card in stack){
            stack[card].style.left = (e.clientX - parent_rect.x - offsetX) + "px";
            stack[card].style.top = (e.clientY - parent_rect.y - offsetY + +card*50) + "px";
        }

    }

});

document.addEventListener("mouseup", (e) => {
    //Chuyển stack bài về cột khi thả
    if(stack){ 
        let element = document.elementFromPoint(e.clientX, e.clientY);
        let column = element.closest(".column");
        let slot   = element.closest(".slot")
        if(column){
            if(!column.lastElementChild || column.lastElementChild && canStack(stack[0],column.lastElementChild)){
                for(let card of stack)
                    column.appendChild(card);
            }
        }
        else if(slot && stack.length == 1){
            if(slot.parentElement.classList.contains("freecell") && slot.childElementCount == 0){
                    slot.appendChild(stack[0]);
            }
            else if(slot.parentElement.classList.contains("foundationcell")){
                if(stack[0].dataset.suit === slot.id && +cardRank(stack[0]) === +slot.dataset.value + 1){
                    slot.appendChild(stack[0]);
                    slot.dataset.value = +slot.dataset.value + 1;
                }
            }
        }


        let parent = stack[0].parentElement;
        console.log(parent.classList);
        if(parent.classList.contains("column")){
            for(i in stack){
                stack[i].style.left = "0px";;
                stack[i].style.zIndex = 0;
                stack[i].style.pointerEvents = "auto";
                stack[i].style.top = (parent.childElementCount - (stack.length - +i)) * 50 + "px";
            }
        }
        else{
            stack[0].style.left = "0px";;
            stack[0].style.zIndex = 0;
            stack[0].style.top = "0px";
            if(parent.parentElement.classList.contains("freecell")){
                stack[0].style.pointerEvents = "auto";
            }
        }

    }
    
    stack = null;
});

document.getElementById("newgame").onclick = async function (){
    location.href = "/new-game";
}
document.getElementById("restart").onclick = async function (){
    location.href = "/";
}


