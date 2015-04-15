var userProfilePage = 1;
var page = 1;
var userPage = 1;
var colors = ["#B7D085", "#F9EBB5", "#D3102E", "#DCD6D5", "#39272A", "#27ACBE", "#3D9275", "#C7E1B8", "#BEC25D"];
var userIndustries = {}
var userLocations = {}
var user_school_connections = {}
var user_company_connections = {}

var UserProfileResults = React.createClass({displayName: "UserProfileResults",
    getInitialState: function() {
        var data = [];
        var prospects = [];
        return {data: data,
                prospects:prospects};
    },
    componentDidMount: function() {
        userProfilePage++;
        var offset = 50 * (userProfilePage - 1);
        var limit = offset + 50;
        this.setState({prospects:this.props.data.splice(offset, limit)})
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
        $("#more-prospects").click(function() {
            userProfilePage++;
            var offset = 50 * (userPage - 1);
            var limit = offset + 50;
            var data = this.props.data.splice(offset, limit);
            if (data.length > 0) {
                result.setState({prospects:data});
                result.bindButtons();
                $("html, body").animate({
                    scrollTop: $(".results").position().top
                }, 100);
            } else {
                bootbox.alert("There are no more Prospects");
                return false;
            }
        });
    },
    render: function() {
    var prospects = this.state.prospects.map(function(prospect) {

        return (
                React.createElement(UserProspect, {data: prospect})
            )
    });
    if (this.props.data.length < 1) {
        return (
          React.createElement("div", {className: "results prospect-profile-results"}, 
              React.createElement("div", {className: "wrapper"}, 
                  React.createElement("div", {className: "empty"}, 
                      React.createElement("h2", null, "There are no more prospects in your network")
                      )
                  ), 
              React.createElement("div", {className: "clear"})
          )
        );
    } else {
        return (
          React.createElement("div", {className: "results prospect-profile-results"}, 
            React.createElement("div", {className: "wrapper"}, 
                React.createElement("div", {className: "stats"}, 
                  React.createElement("div", {className: "stat", id: "u-one"}, 
                    React.createElement("h5", null, "Work Connections"), 
                    React.createElement("canvas", {id: "one"})
                  ), 
                  React.createElement("div", {className: "stat", id: "u-two"}, 
                    React.createElement("h5", null, "School Connections"), 
                    React.createElement("canvas", {id: "two"})
                  ), 
                  React.createElement("div", {className: "stat", id: "u-three"}, 
                    React.createElement("h5", null, "Industry Analysis"), 
                    React.createElement("canvas", {id: "three"})
                  ), 
                  React.createElement("div", {className: "stat", id: "u-four"}, 
                    React.createElement("h5", null, "Location Analysis"), 
                    React.createElement("canvas", {id: "four"})
                  )
                ), 
                prospects, 
                React.createElement("div", {className: "clear"}), 
                React.createElement("button", {className: "btn btn-success", id: "more-prospects"}, "More")
              )
          )
        );
    }
  }
});

var ProfileSalary = React.createClass({displayName: "ProfileSalary",
    render: function() {
        return (
            React.createElement("div", {className: "salaryList"}, 
            React.createElement("h4", null, "Estimated Salary Information"), 
            React.createElement("h3", null, this.props.salary, " *"), 
            React.createElement("p", null, "* This information is based on industry averages.")
            )
            );
    }
});

var ProfileNews = React.createClass({displayName: "ProfileNews",
    render: function() {
    var newsNodes = this.props.data.map(function (news) {
        return (
            React.createElement("div", {className: "news"}, 
                React.createElement("h3", null, news.Title), 
                React.createElement("h5", null, React.createElement("a", {href: ""}, news.Url)), 
                React.createElement("p", null, news.Description)
            )
            )
    });
    return (
        React.createElement("div", {className: "newsList"}, 
            React.createElement("h4", null, "Relevant Links and News"), 
            newsNodes
        )
        )
    }
});

var ProfileSchools = React.createClass({displayName: "ProfileSchools",
    render: function() {
    var schoolNodes = this.props.data.map(function (school) {
        return (
            React.createElement("div", {className: "education"}, 
                React.createElement("h3", null, school.school_name), 
                React.createElement("p", null, school.degree, " - ", school.graduation)
            )
            )
    });
    return (
      React.createElement("div", {className: "schoolList"}, 
        React.createElement("h4", null, "Education History"), 
        schoolNodes
      )
    );
  }
});

var ProfileJobs = React.createClass({displayName: "ProfileJobs",
    render: function() {
    var jobNodes = this.props.data.map(function (job) {
        return (
            React.createElement("div", {className: "job"}, 
                React.createElement("h3", null, job.company_name), 
                React.createElement("p", null, job.title, " - ", job.location, " - ", job.dates)
            )
            )
    });
    return (
      React.createElement("div", {className: "jobsList"}, 
        React.createElement("h4", null, "Work History"), 
        jobNodes
      )
    );
  }
});


var Profile = React.createClass({displayName: "Profile",
    loadProfileFromServer: function() {
        $.ajax({
          url: this.props.url,
          dataType: 'json',
          success: function(data) {
            this.setState({data: data.prospect, client_lists:data.client_lists});
          }.bind(this),
          error: function(xhr, status, err) {
          }.bind(this)
        });
    },
    getInitialState: function() {
        return {data:{"jobs":[],"news": [], "schools": []}, client_lists:[]};
    },
    componentDidMount: function() {
        this.loadProfileFromServer();
        setTimeout(this.loadInLinkedinScript, 1000);
        this.bindButtons();
    },
    loadInLinkedinScript: function() {
        var $html = $('<script type="IN/MemberProfile" data-id="' + this.props.linkedin_url + '" data-related="false" data-format="inline"></script>')
        $(".leftTop").append($html);
        IN.parse(document.body);
    },
    bindButtons: function() {
        var result = this;
        $(".add-prospect").click(function() {
        });

        $(".remove-prospect").click(function() {
        });

        $("#show-user-profile").click(function() {
            $(".user-profile-tabs li").removeClass("active");
            $(this).parent().addClass("active");
            $(".prospect-profile-results").hide();
            $(".profile-content").fadeIn();

        });

        $("#show-user-prospects").click(function() {
            $(".user-profile-tabs li").removeClass("active");
            $(this).parent().addClass("active");
            $(".profile-content").hide();
            $(".prospect-profile-results").fadeIn();
        });
    },
    render: function() {
    var prospectId = this.state.data.id
    var results = this.state.data.results;
    var results = [];
    if (this.state.client_lists) {
        var clientLists = this.state.client_lists.map(function(cl) {
            return (
                React.createElement("h4", null, "Select:",  
                React.createElement("a", {href: "javascript:addToList();", className: "add-to-list", "data-id": cl.id, "data-prospect-id": prospectId}, " ", cl.name)
                )
                )
        });
    }
    return (
      React.createElement("div", {className: "profileBox"}, 
        React.createElement("div", {className: "top"}, 
          React.createElement("div", {className: "wrapper"}, 
                React.createElement("p", null, "Investor Profile ", React.createElement("a", {"data-name": "closeoverlay", href: "#"}, React.createElement("i", {className: "fa fa-times-circle-o"})))
            )
        ), 
        React.createElement("div", {className: "inner"}, 
            React.createElement("div", {className: "wrapper"}, 
                React.createElement("div", {className: "leftTop"}
                ), 
                React.createElement("div", {className: "rightTop"}, 
                    React.createElement("div", {className: "group"}, 
                        React.createElement("h1", null, this.state.data.name), 
                        React.createElement("p", null, this.state.data.location, " | ", this.state.data.industry)
                    ), 
                    React.createElement("div", {className: "group"}, 
                        React.createElement("h4", {className: "wealth"}, "Wealthscore: ", React.createElement("span", {className: "inner"}, this.state.data.wealthscore))
                    ), 
                    React.createElement("div", {className: "clear"}), 
                    React.createElement("a", {href: "javascript:;"}, React.createElement("button", {className: "btn btn-success prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                    React.createElement("a", {"data-skip": this.state.data.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), " Skip Prospect")), 
                    React.createElement("div", {className: "clear"}), 
                    React.createElement("fieldset", {className: "hidden-select"}, 
                        clientLists, 
                        React.createElement("div", null, 
                            React.createElement("input", {type: "text", className: "form-group", id: "new-list-name", placeholder: "enter name"}), React.createElement("button", {id: "create-new", "data-prospect-id": prospectId, className: "btn btn-success"}, "Create New +")
                        )
                    ), 
                    React.createElement("div", {className: "clear"})
                ), 
                React.createElement("hr", null), 
                React.createElement("ul", {className: "tabs user-profile-tabs"}, 
                    React.createElement("li", {className: "active"}, React.createElement("a", {href: "javascript:;", id: "show-user-profile"}, "Profile")), 
                    React.createElement("li", null, React.createElement("a", {href: "javascript:;", id: "show-user-prospects"}, "Relevant Prospects"))
                ), 
                React.createElement("div", {className: "profile-content"}, 
                    React.createElement(ProfileJobs, {data: this.state.data.jobs}), 
                    React.createElement(ProfileSchools, {data: this.state.data.schools}), 
                    React.createElement("div", {className: "clear"}), 
                    React.createElement("hr", null), 
                    React.createElement(ProfileNews, {data: this.state.data.news}), 
                    React.createElement("div", {className: "clear"})
                ), 
                React.createElement(UserProfileResults, {data: results})
            )
        )
      )
    );
  }
});


function loadProfile(id, linkedin_url) {

    $(".overlay").show();
    $("#person").show();
    $("html, body").animate({
        scrollTop: 0
    }, 100);

    url = "/ajax/prospect/" + id;
    React.render(
        React.createElement(Profile, {url: url, linkedin_url: linkedin_url}),
        document.getElementById('person')
    );
    IN.parse();
    $("[data-name='closeoverlay']").on("click", function() {
        closeProfile();
    });
    //bindProspectRequest();
    bindClientListButtons();
}

function closeProfile() {
    $(".overlay").fadeOut();
    $("#person").html("");
}

function bindClientListButtons() {
    $(function() {
        $(".chosen-select").chosen({width: "95%"}); 
        $("button.prospect-add").click(function(e) {
            $(".hidden-select").slideDown();
            addToList();
        });
    });
}

function addToList() {
    $(".add-to-list").click(function() {
        var id = $(this).data("id");
        var prospectId = $(this).data("prospect-id")
        $.post("/user/" + id + "/prospect/add/" + prospectId, function(data) {
            closeProfile();
            bootbox.alert("Client Processed!");
        })
    });

    $("#create-new").click(function() {
        var name = $("#new-list-name").val();
        var prospectId = $(this).data("prospect-id")
        params= {"name": name,
                "create_new": true}
        $.post("/user/1/prospect/add/" + prospectId, params, function(data) {
            closeProfile();
            bootbox.alert("Client Processed!");
        });
    });
}

//This is a dupe function, needs to be combined into one function with app.js
function buildProfileGraphs() {

    var sortableIndustry = []
    var sortableLocation = []

    //lets sort dict so we only get 10 industries max
    for (var industry in userIndustries) {
        sortableIndustry.push([industry, userIndustries[industry]])
    }
    sortableIndustry.sort(function(a, b) {return b[1] - a[1]})
    industries = {}

    for (var location in userLocations) {
        sortableLocation.push([location, userLocations[location]])
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
    for (var wKey in user_company_connections) {
        workData.push({
            value: company_connections[wKey],
            color: randColor(colors),
            label: wKey});
    }

    var schoolData = [];
    for (var sKey in user_school_connections) {
        schoolData.push({
            value: school_connections[sKey],
            color: randColor(colors),
            label: sKey});
    }

    var industryData = [];
    for (var iKey in userIndustries) {
        industryData.push({
            value: industries[iKey],
            color: randColor(colors),
            label: iKey});
    }

    var locationData = [];
    for (var lKey in userLocations) {
        locationData.push({
            value: locations[lKey],
            color: randColor(colors),
            label: lKey});
    }

    if (workData.length > 0) {
        var workChart = new Chart($('canvas#user-one').get(0).getContext("2d")).Doughnut(workData, {});
    } else {
        $("#u-one").append("<h5>No Data</h5>").find("canvas").hide();
    }

    if (schoolData.length > 0) {
        var schoolChart = new Chart($('canvas#user-two').get(0).getContext("2d")).Doughnut(schoolData);
    } else {
        $("#u-two").append("<h5>No Data</h5>").find("canvas").hide();
    }

    var industryChart = new Chart($('canvas#user-three').get(0).getContext("2d")).Doughnut(industryData, {});
    var locationChart = new Chart($('canvas#user-four').get(0).getContext("2d")).Doughnut(locationData, {});
}

