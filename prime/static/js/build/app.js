var industries = {}
var offset = 0;
var colors = ["#B7D085", "#F9EBB5", "#D3102E", "#DCD6D5", "#39272A", "#27ACBE", "#3D9275", "#C7E1B8", "#BEC25D"];
var locations = {}
var school_connections = {}
var company_connections = {}

function randColor(colors) {
    return colors[Math.floor(Math.random() * colors.length)]
}

var Relationship = React.createClass({displayName: "Relationship",
    render: function() {
        return (
            React.createElement("p", null, "You are connected via ", React.createElement("a", {href: this.props.url}, this.props.name), ". ", React.createElement("a", {className: "small", href: this.props.url}, "View more people like this"))
            )
    }
});

var Results = React.createClass({displayName: "Results",
    loadProfileFromServer: function() {
        $.ajax({
          url: this.props.url,
          dataType: 'json',
          success: function(data) {
            this.setState({data: data.prospect, client_lists:data.client_lists});
          }.bind(this),
          error: function(xhr, status, err) {
            console.log(data)
            console.error(this.props.url, status, err.toString());
          }.bind(this)
        });
    },
    getInitialState: function() {
        return {data:[]};
    },
    componentDidMount: function() {
        setTimeout(this.loadInLinkedinScript, 1000);
    },
    loadInLinkedinScript: function() {
        //IN.parse(document.body);
    },
    render: function() {
    var prospects = this.props.data.map(function(prospect) {
        if (prospect.company_name) {
            var job = prospect.title + ", " + prospect.company_name;
        } else {
            var job = "N/A"
        }

        if (prospect.company_name) {
            var url = "/company/" + prospect.company_id;
            var relationship = React.createElement(Relationship, {name: prospect.company_name, url: url})
        } else {
            var url = "/school/" + prospect.school_id;
            var relationship = React.createElement(Relationship, {name: prospect.school_name, url: url})
        }
        return (
            React.createElement("div", {className: "result"}, 
                React.createElement("div", {className: "first"}
                ), 
                React.createElement("div", {className: "second"}, 
                    React.createElement("h3", null, React.createElement("a", {"data-prospect": prospect.id, "data-url": prospect.url}, prospect.prospect_name)), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Job:"), " ", job), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Location:"), " ", prospect.current_location), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Industry:"), " ", prospect.current_industry)
                ), 
                React.createElement("div", {className: "image"}, 
                    React.createElement("img", {src: prospect.image_url})
                ), 
                React.createElement("div", {className: "connections"}, 
                    React.createElement("h5", null, "Connection Path"), 
                    relationship
                ), 
                React.createElement("div", {className: "buttons"}, 
                    React.createElement("a", {href: "javascript:;"}, React.createElement("button", {className: "btn btn-success prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                    React.createElement("a", {href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), " Skip Prospect"))
                ), 
                React.createElement("div", {className: "clear"})
            )
            )
    });
    return (
      React.createElement("div", {className: "results"}, 
        prospects
      )
    );
  }
});



function buildResults() {
    var data = window._userData.results;
    var limit = offset + 20;
    React.render(
        React.createElement(Results, {data: data}),
        document.getElementById('prospects')
    );
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
    bindButtons();
    bindProfiles();
});

function bindProfiles() {
    $("[data-prospect]").click(function() {
        var url = $(this).data('url');
        var id = $(this).data("prospect");
        loadProfile(id, url);
    });
}

function buildGraphs() {

    var sortableIndustry = []
    var sortableLocation = []

    //lets sort dict so we only get 10 industries max
    for (var industry in industries) {
        sortableIndustry.push([industry, industries[industry]])
    }
    sortableIndustry.sort(function(a, b) {return b[1] - a[1]})
    industries = {}

    for (var location in locations) {
        sortableLocation.push([location, locations[location]])
    }

    sortableLocation.sort(function(a, b) {return b[1] - a[1]})
    locations = {}

    //If less than 10, we need to do the length
    var industryLimit = (sortableIndustry.length > 10) ? 10 : sortableIndustry.length;
    var locationLimit = (sortableLocation.length > 10) ? 10 : sortableLocation.length;

    for (var i=0;i<industryLimit;i++) {
        industries[sortableIndustry[i][0]] = sortableIndustry[i][1]
    }

    for (var i=0;i<locationLimit;i++) {
        locations[sortableLocation[i][0]] = sortableLocation[i][1]
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


function bindButtons() {
    $("#show-analytics").click(function() {
        $(".results-dashboard").hide();
        $(".stats").fadeIn();
        $(".tabs li").removeClass("active");
        $(this).parent().addClass("active");
    });

    $("#show-leads").click(function() {
        $(".stats").hide();
        $(".results-dashboard").fadeIn();
        $(".tabs li").removeClass("active");
        $(this).parent().addClass("active");
    });
}

function hideOverlay() {
    $(".overlay").hide();
}

