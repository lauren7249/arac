var gdata = {
    "name":"James Johnson",
    "jobs": [{"company_name":"Delaware Investments","title": "Developer", "location": "New York", "dates": "2006 - 2013"},{"company_name":"YouRenew","location":"New Haven", "dates": "2014","title": "Developer"}],
    "schools": [{"school_name": "Yale University", "graduation": "2009", "degree": "History"},{"school_name":"St Josephs Prep","degree": "Highschool", "graduation":"1005"}],
    "industry": "Software",
    "location": "New York",
    "connections": "500",
    "url":"http://www.linkedin.com/pub/james-johnson/a/431/7a0",
    "news": [{"title": "James is awesome", "url":"http://awesome.com", "description":"This is a piece of text that is supposed to be long and good"}, {"title": "James is okay", "url":"http://okay.com", "description":"This is a piece of text that is supposed to be long and good"}],
    "salary": "$150,000",
    "wealthscore": "98/100"

}

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
            this.setState({data: data});
          }.bind(this),
          error: function(xhr, status, err) {
            console.log(data)
            console.error(this.props.url, status, err.toString());
          }.bind(this)
        });
    },
    getInitialState: function() {
        return {data:{"jobs":[],"news": [], "schools": []}};
    },
    componentDidMount: function() {
        this.loadProfileFromServer();
        setTimeout(this.loadInLinkedinScript, 1000);
    },
    loadInLinkedinScript: function() {
        var $html = $('<script type="IN/MemberProfile" data-id="' + this.props.linkedin_url + '" data-related="false" data-format="inline"></script>')
        $(".leftTop").append($html);
        IN.parse(document.body);
    },
    render: function() {
    return (
      React.createElement("div", {className: "profileBox"}, 
        React.createElement("div", {className: "top"}, 
            React.createElement("p", null, "Investor Profile ", React.createElement("a", {"data-name": "closeoverlay", href: "#"}, React.createElement("i", {className: "fa fa-times-circle-o"})))
        ), 
        React.createElement("div", {className: "inner"}, 
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
                React.createElement("a", {"data-success": this.state.data.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-success"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                React.createElement("a", {"data-skip": this.state.data.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), " Skip Prospect")), 
                React.createElement("a", {href: "javascript:;"}, React.createElement("button", {className: "btn btn-primary prospect-request"}, React.createElement("input", {type: "hidden", value: this.state.data.id}), React.createElement("i", {className: "fa fa-info-circle"}), " Request Contact Information"))
            ), 
            React.createElement("hr", null), 
            React.createElement(ProfileJobs, {data: this.state.data.jobs}), 
            React.createElement(ProfileSchools, {data: this.state.data.schools}), 
            React.createElement("div", {className: "clear"}), 
            React.createElement("hr", null), 
            React.createElement(ProfileNews, {data: this.state.data.news}), 
            React.createElement(ProfileSalary, {salary: this.state.data.salary}), 
            React.createElement("div", {className: "clear"})
        )
      )
    );
  }
});


function loadProfile(id, linkedin_url) {

    $(".overlay").show();

    url = "/ajax/prospect/" + id;
    React.render(
        React.createElement(Profile, {url: url, linkedin_url: linkedin_url}),
        document.getElementById('person')
    );
    IN.parse();
    $("[data-name='closeoverlay']").on("click", function() {
        closeProfile();
    });
    bindProspectRequest();
}

function closeProfile() {
    $(".overlay").fadeOut();
    $("#person").html("");
}

function bindProspectRequest() {
    $("button.prospect-request").click(function(e) {
        var val = $(this).find("input").val()
        $.get("/ajax/pipl/" + val, function(data) {
            alert("email:" + data.email);
        });
    });
}
