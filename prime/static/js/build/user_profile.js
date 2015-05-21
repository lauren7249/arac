var industries = {}
var type = "extended"
var page = 1;
var userPage = 1;
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
            React.createElement("p", null, React.createElement("a", {href: this.props.url}, this.props.name), ".")
            )
    }
});


var UserProspect = React.createClass({displayName: "UserProspect",
    render: function() {
        var prospect = this.props.data;
        var relationship = React.createElement(Relationship, {name: prospect.relationship})
        var URL = "/prospect/" + prospect.id
        return (
            React.createElement("div", {className: "result", "data-result": prospect.id}, 
                React.createElement("div", {className: "first"}
                ), 
                React.createElement("div", {className: "second"}, 
                    React.createElement("h3", null, React.createElement("a", {target: "_blank", href: URL, "data-url": prospect.url}, prospect.prospect_name)), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Job:"), " ", prospect.company_name), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Location:"), " ", prospect.current_location), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Industry:"), " ", prospect.current_industry)
                ), 
                React.createElement("div", {className: "image"}, 
                    React.createElement("p", null, "Lead Score"), 
                    React.createElement("h4", {className: "money"}, prospect.wealthscore)
                ), 
                React.createElement("div", {className: "connections"}, 
                    React.createElement("h5", null, "Relevancy"), 
                    relationship
                ), 
                React.createElement("div", {className: "buttons"}, 
                    React.createElement("a", {className: "add-prospect", "data-id": prospect.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-success prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                    React.createElement("a", {className: "remove-prospect", "data-id": prospect.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), " Not A Good Fit"))
                ), 
                React.createElement("div", {className: "clear"})
            )
            )
    }
});

var Prospect = React.createClass({displayName: "Prospect",
    render: function() {
        var prospect = this.props.data;
        var relationship = React.createElement(Relationship, {name: prospect.relevancy})
        var URL = "/prospect/" + prospect.data.id
        return (
            React.createElement("div", {className: "result", "data-result": prospect.data.id}, 
                React.createElement("div", {className: "first"}
                ), 
                React.createElement("div", {className: "second"}, 
                    React.createElement("h3", null, React.createElement("a", {target: "_blank", href: URL, "data-url": prospect.url}, prospect.data.name)), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Job:"), " ", prospect.data.current_job), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Location:"), " ", prospect.data.location), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Industry:"), " ", prospect.data.industry)
                ), 
                React.createElement("div", {className: "image"}, 
                    React.createElement("p", null, "Lead Score"), 
                    React.createElement("h4", {className: "money"}, prospect.data.wealthscore)
                ), 
                React.createElement("div", {className: "connections"}, 
                    React.createElement("h5", null, "Relevancy"), 
                    relationship
                ), 
                React.createElement("div", {className: "buttons"}, 
                    React.createElement("a", {className: "add-prospect", "data-id": prospect.data.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-success prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                    React.createElement("a", {className: "remove-prospect", "data-id": prospect.data.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), "  Not A Good Fit"))
                ), 
                React.createElement("div", {className: "clear"})
            )
            )
    }
});


var UserResults = React.createClass({displayName: "UserResults",
    loadProfileFromServer: function() {
        params = {p:userPage,
                type:type}
        $.ajax({
          url: "/prospect/json/" + prospectID,
          data:params,
          dataType: 'json',
          success: function(data) {
              $(".loading").fadeOut();
            this.setProps({data: data.results});
            this.bindButtons();
            this.loadInLinkedinScript();
            $(".loading").hide();
            return false;
          }.bind(this),
          error: function(xhr, status, err) {
            bootbox.alert("Something went wrong! Make sure you enter in search paramaters")
            $(".loading").hide();
            return false;
          }.bind(this)
        });
    },
    getInitialState: function() {
        data = [];
        return {data: data};
    },
    componentDidMount: function() {
        this.loadProfileFromServer()
        this.bindButtons();
    },
    loadInLinkedinScript: function() {
        IN.parse(document.body);
    },
    bindButtons: function() {
        var result = this;
        $(".add-prospect").click(function() {
            var id = $(this).data("id");
            $.post("/user/prospect/add/" + id, function(data) {
                $("[data-result='" + id + "']").fadeOut();
            });
        });

        $(".remove-prospect").click(function() {
            var id = $(this).data("id");
            $.post("/user/prospect/skip/" + id, function(data) {
                $("[data-result='" + id + "']").fadeOut();
            });
        });
        $("#more-prospects").click(function(event) {
            if (event.handled !== true) {
                userPage++;
                $("html, body").animate({
                    scrollTop: $(".results").position().top
                }, 100);
                result.loadProfileFromServer();
                event.handled = true;
            }
            return false
        });

        $("#extended").click(function(event) {
            if (event.handled !== true) {
                $(".loading").show();
                userPage = 1
                $(".headers a").removeClass("active");
                $(this).addClass("active")
                $(".stats").hide();
                $(".user-holder").fadeIn();
                type = "extended"
                result.loadProfileFromServer()
                event.handled = true;
            }
            return false
        });

        $("#first").click(function(event) {
            console.log("happening");
            if (event.handled !== true) {
                $(".loading").show();
                userPage = 1
                $(".headers a").removeClass("active");
                $(this).addClass("active")
                $(".stats").hide();
                $(".user-holder").fadeIn();
                type = "first"
                result.loadProfileFromServer()
                event.handled = true;
            }
            return false
        });

        $("#network").click(function() {
            if (event.handled !== true) {
                $(".headers a").removeClass("active");
                $(this).addClass("active")
                $(".user-holder").hide();
                $(".stats").fadeIn();
                buildGraphs();
                event.handled = true;
            }
            return false
        });
    },
    render: function() {
    var prospects = this.props.data.map(function(prospect) {
        if (prospect.data != undefined) {
            return (
                    React.createElement(Prospect, {data: prospect})
                )
        } else {
            return (
                    React.createElement(UserProspect, {data: prospect})
                )
        }
    });
    if (this.props.data.length < 1) {
        return (
          React.createElement("div", {className: "results"}, 
              React.createElement("div", {className: "wrapper"}, 
                  React.createElement("div", {className: "loading", id: "show-always"}, 
                      React.createElement("h2", null, "Loading ", React.createElement("img", {src: "/static/img/loader.gif"})), 
                      React.createElement("p", null, "Fetching Prospects")
                  ), 
                  React.createElement("div", {className: "empty"}, 
                      React.createElement("h2", null, "There are no more prospects in this network")
                      )
                  ), 
              React.createElement("div", {className: "clear"})
          )
        );
    } else {
        return (
          React.createElement("div", {className: "results"}, 
            React.createElement("div", {className: "wrapper"}, 
                prospects, 
                React.createElement("div", {className: "clear"}), 
                React.createElement("button", {className: "btn btn-success", id: "more-prospects"}, "More")
              )
          )
        );
    }
  }
});


function buildResults() {
    var data = []
    React.render(
        React.createElement(UserResults, {data: data}),
        document.getElementById('user-prospects')
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
    bindSearch();
    bindDates();
});

function buildGraphs() {

    $.ajax({
        url: "/network?prospect_id=" + prospectID,
        type: 'GET',
        cache: false,
        timeout: 30000,
        error: function(){
            return true;
        },
        success: function(data){ 
            var user_industries = data.user_data.industries
            var user_locations = data.user_data.locations
            var user_schools = data.user_data.schools
            var user_jobs = data.user_data.jobs

            var extended_user_industries = data.extended_user_data.industries
            var extended_user_locations = data.extended_user_data.locations
            var extended_user_schools = data.extended_user_data.schools
            var extended_user_jobs = data.extended_user_data.jobs

            for (var key in data.user_data) {
                buildGraph(key, data.user_data[key], 'user')
            }

            for (var key in data.extended_user_data) {
                buildGraph(key, data.extended_user_data[key], 'extended-user')
            }
        }
    });

}

function buildGraph(name ,data, prefix) {
    var arr = []
    var $div = $("#" + prefix + "-" + name)
    var $canvas = $div.find("canvas")
    for (var key in data) {
        arr.push({
            value: data[key],
            color: randColor(colors),
            label: key});
    }

    if (arr.length > 0) {
        try {
            var chart = new Chart($canvas.get(0).getContext("2d")).Doughnut(arr, {});
        } catch(err) {
        }
    } else {
        try {
            $div.find("h5").html("No Data") 
        } catch(err) {
            $div.append("<h5>No Data</h5>").find("canvas").hide();
        }
    }
}

function hideOverlay() {
    $(".overlay").hide();
}

function bindSearch() {
    companySearch();
    schoolSearch();
    locationSearch();
    bindSlider();
}

function companySearch() {
    var $valuesautocomplete = $("#company_ids");
    var $autocomplete = $("#company-autocomplete");
    $autocomplete.autocomplete({
        source: function(request, response) {
            var val = request.term
            $.getJSON("search.json?q=" + val, function(data) {
                return response(data.data.slice(0, 8))
            })
        },
        select: function(event, ui) {
            var span  = $("<li data-company='"  + ui.item.id + "' class='styled'><span>" + ui.item.name + "</span><a href='javascript:removeSpan(1, " + ui.item.id + ");'>X</a></li>")
            $("ul.company-search").prepend(span);
            var ids = $valuesautocomplete.val().split();
            var new_ids = []
            for (var j in ids) {
                if (ids[j] !=="") {
                    new_ids.push(ids[j])
                }
            }
            new_ids.push(ui.item.id)
            $valuesautocomplete.val(new_ids.join(","))

        },
        appendTo: '#company-results-autocomplete'
    }).autocomplete( "instance" )._renderItem = function( ul, item ) {
      return $( "<li>" )
        .data('item.autocomplete', item)
        .append( "<a data-id='" + item.id + "'>" + item.name + "<p><span>" + item.count + "</span> members</p></a>" )
        .appendTo( ul );
    }
}

function schoolSearch() {
    var $valuesautocomplete = $("#school_ids");
    var $autocomplete = $("#school-autocomplete");
    $autocomplete.autocomplete({
        source: function(request, response) {
            var val = request.term
            $.getJSON("search.json?type=0&q=" + val, function(data) {
                return response(data.data.slice(0, 8))
            })
        },
        select: function(event, ui) {
            var span  = $("<li data-school='"  + ui.item.id + "' class='styled'><span>" + ui.item.name + "</span><a href='javascript:removeSpan(2, " + ui.item.id + ");'>X</a></li>")
            $("ul.school-search").prepend(span);
            var ids = $valuesautocomplete.val().split();
            var new_ids = []
            for (var j in ids) {
                if (ids[j] !=="") {
                    new_ids.push(ids[j])
                }
            }
            new_ids.push(ui.item.id)
            $valuesautocomplete.val(new_ids.join(","))

        },
        appendTo: '#school-results-autocomplete'
    }).autocomplete( "instance" )._renderItem = function( ul, item ) {
      return $( "<li>" )
        .data('item.autocomplete', item)
        .append( "<a data-id='" + item.id + "'>" + item.name + "<p><span>" + item.count + "</span> members</p></a>" )
        .appendTo( ul );
    }
}

function locationSearch() {
    var $valuesautocomplete = $("#location_ids");
    var $autocomplete = $("#location-autocomplete");
    $autocomplete.autocomplete({
        source: function(request, response) {
            var val = request.term
            $.getJSON("search.json?type=2&q=" + val, function(data) {
                return response(data.data.slice(0, 8))
            })
        },
        select: function(event, ui) {
            var span  = $("<li data-location='"  + ui.item.name + "' class='styled'><span>" + ui.item.name + "</span><a href='javascript:removeSpan(3, \"" + ui.item.name + "\");'>X</a></li>")
            $("ul.location-search").prepend(span);
            var ids = $valuesautocomplete.val().split();
            var new_ids = []
            for (var j in ids) {
                if (ids[j] !=="") {
                    new_ids.push(ids[j])
                }
            }
            new_ids.push(ui.item.id)
            $valuesautocomplete.val(new_ids.join(","))

        },
        appendTo: '#location-results-autocomplete'
    }).autocomplete( "instance" )._renderItem = function( ul, item ) {
      return $( "<li>" )
        .data('item.autocomplete', item)
        .append( "<a data-id='" + item.id + "'>" + item.name + "<p>" )
        .appendTo( ul );
    }
}

function removeSpan(spanType, id) {
    if (spanType == 1) {
        $("[data-company='" + id + "']").remove();
        var ids = $("#company_ids").val().split(",");
        var index = ids.indexOf(id.toString())
        if (index > -1) {
            ids.splice(index, 1)
        }
        $("#company_ids").val(ids.join(","))
        return;
    }

    if (spanType == 2) {
        $("[data-school='" + id + "']").remove();
        var ids = $("#school_ids").val().split(",");
        var index = ids.indexOf(id.toString())
        if (index > -1) {
            ids.splice(index, 1)
        }
        $("#school_ids").val(ids.join(","))
        return;
    }

    if (spanType == 3) {
        $("[data-location='" + id + "']").remove();
        var ids = $("#location_ids").val().split(",");
        var index = ids.indexOf(id.toString())
        if (index > -1) {
            ids.splice(index, 1)
        }
        $("#location_ids").val(ids.join(","))
        return;
    }
}


function bindDates() {
    $('.datepicker').datepicker({
        changeYear: true,
        changeMonth: true
    });
}

function bindSlider() {
    $( "#slider-range" ).slider({
        range: "min",
        min: 35,
        max: 100,
        value: 49,
        slide: function( event, ui ) {
            $( "#amount" ).val(ui.value);
        }
    });
}

function newSearch() {
    $(".dashboard-search").slideDown();
    $(".new-search").hide();
    $("#prev").hide();
    $("#next").hide();
}