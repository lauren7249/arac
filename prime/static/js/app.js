var industries = {}
var offset = 0;
var colors = ["#B7D085", "#F9EBB5", "#D3102E", "#DCD6D5", "#39272A", "#27ACBE", "#3D9275", "#C7E1B8", "#BEC25D"];
var locations = {}
var school_connections = {}
var company_connections = {}

function randColor(colors) {
    return colors[Math.floor(Math.random() * colors.length)]
}

function resultHTML(result) {
    var $parent = $("<div class='result'></div>");
    var $h3 = $("<h3><a result-prospect='" + result.url + "' href='javascript:loadProfile(" + result.id + ");'>" + result.prospect_name + "</a>");
    var $h5 = $("<h5>" + result.relationship + "</h5>")
    if (result.company_name) {
        var $entity = $("<a href='/company/" + result.company_id + "'><button class='btn btn-success'>" + result.company_name + "</button></a>")
    } else {
        var $entity = $("<a href='/school/" + result.school_id + "'><button class='btn btn-success'>" + result.school_name + "</button></a>")
    }

    var $more = $("<a href='javascript:;'><button class='btn btn-primary'>" + result.current_industry + "</button></a><a href='javascript:;'><button class='btn btn-warning'>" + result.current_location + "</button></a>")
    return $parent.append($h3).append($h5).append($entity).append($more)
}

function buildResults() {
    data = window._userData.results;
    var limit = offset + 20;
    var $result = $("div.results");
    for (var a in data) {
        if (a < limit) {
            $result.append(resultHTML(data[a]))
        }
        calculateResults(data[a])
    }
    offset+=20;
}

function calculateResults(data) {

    //Calculate Industry
    if (data.current_industry in industries) {
        var iCount = industries[data.current_industry]
        iCount++;
        industries[data.current_industry] = iCount;
    } else {
        var iCount = 1;
        industries[data.current_industry] = iCount;
    }

    //Calculate Location
    if (data.current_location in locations) {
        var iCount = locations[data.current_location]
        iCount++;
        locations[data.current_location] = iCount;
    } else {
        var iCount = 1;
        locations[data.current_location] = iCount;
    }

    if (data.school_name) {
        //Calculate School Connections
        if (data.school_name in school_connections) {
            var iCount = school_connections[data.school_name]
            iCount++;
            school_connections[data.school_name] = iCount;
        } else {
            var iCount = 1;
            school_connections[data.school_name] = iCount;
        }
    }

    if (data.company_name) {

        if (data.company_name in company_connections) {
            var iCount = company_connections[data.company_name]
            iCount++;
            company_connections[data.company_name] = iCount;
        } else {
            var iCount = 1;
            company_connections[data.company_name] = iCount;
        }
    }
}

$(function() {
    buildResults();
    buildGraphs();
});

function buildGraphs() {

    var sortableIndustry = []

    for (var industry in industry) {
        sortableIndustry.push([industry, industries[industry])
    }
    sortableIndustry.sort(function(a, b) {return a[1] - b[1]})
    industries = {}
    for (var item in 10) {
        industries[sortableIndustry[item][0]] = sortableIndustry[item][1]
    }

    var workData = [];
    for (var wKey in company_connections) {
        workData.push({
            value: company_connections[wKey],
            color: randColor(colors),
            label: wKey});
    }

    var schoolData = [];
    for (var sKey in school_connections) {
        schoolData.push({
            value: school_connections[sKey],
            color: randColor(colors),
            label: sKey});
    }
    console.log(schoolData);

    var industryData = [];
    for (var iKey in industries) {
        industryData.push({
            value: industries[iKey],
            color: randColor(colors),
            label: iKey});
    }

    var locationData = [];
    for (var lKey in locations) {
        locationData.push({
            value: locations[lKey],
            color: randColor(colors),
            label: lKey});
    }

    if (workData.length > 0) {
        var workChart = new Chart($('canvas#one').get(0).getContext("2d")).Doughnut(workData, {});
    } else {
        $("#g-one").append("<h5>No Data</h5>").find("canvas").hide();
    }

    if (schoolData.length > 0) {
        var schoolChart = new Chart($('canvas#two').get(0).getContext("2d")).Doughnut(schoolData);
    } else {
        $("#g-two").append("<h5>No Data</h5>").find("canvas").hide();
    }

    var industryChart = new Chart($('canvas#three').get(0).getContext("2d")).Doughnut(industryData, {});
    var locationChart = new Chart($('canvas#four').get(0).getContext("2d")).Doughnut(locationData, {});
}


