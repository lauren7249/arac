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

var Relationship = React.createClass({
    render: function() {
        return (
            <p><a href={this.props.url}>{this.props.name}</a>.</p>
            )
    }
});


var UserProspect = React.createClass({
    render: function() {
        var prospect = this.props.data;
        var relationship = <Relationship name={prospect.relationship} />
        var URL = "/prospect/" + prospect.id
        return (
            <div className='result' data-result={prospect.id}>
                <div className='first'>
                </div>
                <div className='second'>
                    <h3><a target='_blank' href={URL} data-url={prospect.url}>{prospect.prospect_name}</a></h3>
                    <h4><span className='grey'>Current Job:</span> {prospect.company_name}</h4>
                    <h4><span className='grey'>Current Location:</span> {prospect.current_location}</h4>
                    <h4><span className='grey'>Current Industry:</span> {prospect.current_industry}</h4>
                </div>
                <div className='image'>
                    <p>Lead Score</p>
                    <h4 className='money'>{prospect.wealthscore}</h4>
                </div>
                <div className='connections'>
                    <h5>Relevancy</h5>
                    {relationship}
                </div>
                <div className='buttons'>
                    <a className='add-prospect' data-id={prospect.id} href='javascript:;'><button className='btn btn-success prospect-add'><i className='fa fa-plus'></i> Add To Prospect List</button></a>
                    <a  className='remove-prospect' data-id={prospect.id}  href='javascript:;'><button className='btn btn-danger'><i className='fa fa-chevron-circle-right'></i> Not A Good Fit</button></a>
                </div>
                <div className='clear'></div>
            </div>
            )
    }
});

var Prospect = React.createClass({
    render: function() {
        var prospect = this.props.data;
        var relationship = <Relationship name={prospect.relevancy} />
        var URL = "/prospect/" + prospect.data.id
        return (
            <div className='result' data-result={prospect.data.id}>
                <div className='first'>
                </div>
                <div className='second'>
                    <h3><a target='_blank' href={URL} data-url={prospect.url}>{prospect.data.name}</a></h3>
                    <h4><span className='grey'>Current Job:</span> {prospect.data.current_job}</h4>
                    <h4><span className='grey'>Current Location:</span> {prospect.data.location}</h4>
                    <h4><span className='grey'>Current Industry:</span> {prospect.data.industry}</h4>
                </div>
                <div className='image'>
                    <p>Lead Score</p>
                    <h4 className='money'>{prospect.data.wealthscore}</h4>
                </div>
                <div className='connections'>
                    <h5>Relevancy</h5>
                    {relationship}
                </div>
                <div className='buttons'>
                    <a className='add-prospect' data-id={prospect.data.id} href='javascript:;'><button className='btn btn-success prospect-add'><i className='fa fa-plus'></i> Add To Prospect List</button></a>
                    <a  className='remove-prospect' data-id={prospect.data.id}  href='javascript:;'><button className='btn btn-danger'><i className='fa fa-chevron-circle-right'></i>  Not A Good Fit</button></a>
                </div>
                <div className='clear'></div>
            </div>
            )
    }
});

var Results = React.createClass({
    loadProfileFromServer: function() {
        var companyIDs = $("#company_ids").val()
        var schoolIDs = $("#school_ids").val()
        var title = $("#title").val()
        var name = $("#name").val()
        if (companyIDs == "" && schoolIDs == "" && title == "" && name == "") {
            bootbox.alert("You must enter either one school, a job title or one company.");
            $(".loading").hide();
            return false;
        }
        var job_start = ($("#job_start").val() == "") ? null : $("#job_start").val();
        var job_end = ($("#job_end").val() == "") ? null : $("#job_end").val();
        var params={
            company_ids: companyIDs,
            school_ids: schoolIDs,
            school_end: $("#school_end").val(),
            name: name,
            title: title,
            gender: $("[name='gender']:checked").val(),
            location_ids: $("#location_ids").val(),
            industry_ids: $("#industry_ids").val(),
            wealthscore: $("#amount").val(),
            p:page
        }
        if (job_start) {
            params["job_start"] = job_start;
        }
        if (job_end) {
            params["job_end"] = job_end;
        }
        $.ajax({
          url: "/api",
          data:params,
          dataType: 'json',
          success: function(data) {
            if (data.success.length < 1) {
                bootbox.alert("There are no results for this query");
                return false;
            }
            this.setProps({data: data.success});
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
        return {data:[]};
    },
    componentDidMount: function() {
        setTimeout(this.loadInLinkedinScript, 1000);
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
        $("#big-search").click(function(event) {
            if (event.handled !== true) {
                $(".dashboard-search").slideUp();
                $(".loading").show();
                $(".new-search").show();
                $("#next").show();
                result.loadProfileFromServer()
                event.handled = true;
            }
            return false;
        });

        $("#next").click(function(event) {
            if (event.handled !== true) {
                page += 1;
                $("#prev").show();
                $("html, body").animate({
                    scrollTop: $(".results").position().top
                }, 100);
                result.loadProfileFromServer();
                event.handled = true;
            }
            return false;
        });

        $("#prev").click(function(event) {
            if (event.handled !== true) {
                page--;
                if (page < 1) {
                    page = 1;
                }
                $("html, body").animate({
                    scrollTop: $(".results").position().top
                }, 100);
                result.loadProfileFromServer();
                event.handled = true;
            }
            return false;
        });
    },
    render: function() {
    var prospects = this.props.data.map(function(prospect) {

        return (
                <Prospect data={prospect} />
            )
    });
    if (this.props.data.length < 1) {
        return (
          <div className="results">
            <div className='empty'>
                <h2>Use the search tool to find leads!</h2>
                <p>There are several great ways to use AdvisorConnect to find new leads for your business</p>
                <ul>
                    <li>Look for people with common connections (eg. worked at the same company, went to the same school) who live in your area</li>
                    <li>Focus on companies where you have had previous success</li>
                    <li>Find the whales. Search for high paying job titles at fortune 500 companies.</li>
                </ul>
            </div>

            <div className='clear'></div>
          </div>
        );
    } else {
        return (
          <div className="results">
            {prospects}
            <div className='clear'></div>
          </div>
        );
    }
  }
});

var UserResults = React.createClass({
    loadProfileFromServer: function() {
        params = {p:userPage,
                type:type}
        $.ajax({
          url: "/dashboard/json",
          data:params,
          dataType: 'json',
          success: function(data) {
              $(".loading").fadeOut();
            if (data.results.length < 1) {
                bootbox.alert("There are no results for this query");
                return false;
            }
            this.setProps({data: data.results});
            this.bindButtons();
            this.loadInLinkedinScript();
            $(".loading").hide();
            return false;
          }.bind(this),
          error: function(xhr, status, err) {
              debugger;
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
        $("#more-prospects").click(function() {
            userPage++;
            $("html, body").animate({
                scrollTop: $(".results").position().top
            }, 100);
            result.loadProfileFromServer();
        });

        $("#extended").click(function(event) {
            if (event.handled !== true) {
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
                    <Prospect data={prospect} />
                )
        } else {
            return (
                    <UserProspect data={prospect} />
                )
        }
    });
    if (this.props.data.length < 1) {
        return (
          <div className="results">
              <div className="wrapper">
                  <div className='loading' id='show-always'>
                      <h2>Loading <img src='/static/img/loader.gif' /></h2>
                      <p>Finding the best prospects.</p>
                  </div>
                  <div className='empty'>
                      <h2>There are no more prospects in your network</h2>
                      </div>
                  </div>
              <div className='clear'></div>
          </div>
        );
    } else {
        return (
          <div className="results">
            <div className="wrapper">
                {prospects}
                <div className='clear'></div>
                <button className='btn btn-success' id='more-prospects'>More</button>
              </div>
          </div>
        );
    }
  }
});


function buildResults() {
    var data = []
    React.render(
        <UserResults data={data} />,
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
    bindButtons();
    bindSearch();
    bindDates();
});

function bindButtons() {
    $("#extended").click(function() {
        $(".headers a").removeClass("active");
        $(this).addClass("active")
        $(".stats").hide();
        $(".user-holder").fadeIn();
        type = "extended"
        buildResults();
    });

    $("#first").click(function() {
        $(".headers a").removeClass("active");
        $(this).addClass("active")
        $(".stats").hide();
        $(".user-holder").fadeIn();
        type = "first"
        buildResults();
    });

    $("#network").click(function() {
        $(".headers a").removeClass("active");
        $(this).addClass("active")
        $(".user-holder").hide();
        $(".stats").fadeIn();
        buildGraphs();

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
