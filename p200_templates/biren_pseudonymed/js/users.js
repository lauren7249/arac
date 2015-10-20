var colors = ["#8dd8f7", "#5bbdea", "#01a1dd", "#0079c2"];
function randColor(colors) {
    return colors[Math.floor(Math.random() * colors.length)]
}

var user = 
    {"industries":
        [{label:"Hospitality", value:287, color: randColor(colors)}, {label:"Sports", value:190, color: randColor(colors)}, {label:"Marketing & Advertising", value:144, color: randColor(colors)}, {label:"Retail", value:135, color: randColor(colors)}],
    "companies":
        [{label:"Aramark", value:456, color: randColor(colors)}, {label:"The Madison Square Company", value:115, color: randColor(colors)}],
    "your_contacts":64,
    "extended":2154,
    "total":2794
       }