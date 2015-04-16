var industries = {}
var page = 1;

var Relationship = React.createClass({displayName: "Relationship",
    render: function() {
        return (
            React.createElement("p", null, "You are connected via ", React.createElement("a", {href: this.props.url}, this.props.name), ".")
            )
    }
});

var SocialAccounts = React.createClass({displayName: "SocialAccounts",
    getInitialState: function() {
        return {data:[]};
    },
    render: function() {
        var socialaccounts = this.props.data.map(function(account) {
            var name = "fa fa-" + account.type

            return (
                React.createElement("div", {className: "social"}, 
                    React.createElement("a", {href: account.url}, React.createElement("i", {className: name}), " ", account.typeName)
                )
                );
        });
        return (
            React.createElement("div", {className: "social"}, 
                socialaccounts
            )
            )
    }
});


var Prospect = React.createClass({displayName: "Prospect",
    handleChange: function() {
        var id = this.props.data.id;
        var $div = $("[data-result='" + id + "']")
        if ($div.hasClass("checked")) {
            $div.removeClass("checked");
        } else {
            $div.addClass("checked");
        }
    },
    render: function() {
        var prospect = this.props.data;
        var relationship = React.createElement(Relationship, {name: prospect.relevancy})
        return (
            React.createElement("div", {className: "result checked", "data-result": prospect.id}, 
                React.createElement("div", {className: "first"}, 
                    React.createElement("input", {type: "checkbox", value: prospect.id, defaultChecked: true, onChange: this.handleChange})
                ), 
                React.createElement("div", {className: "second"}, 
                    React.createElement("h3", null, React.createElement("a", {"data-prospect": prospect.id, "data-url": prospect.url}, prospect.name)), 
                    React.createElement("h4", null, React.createElement("i", {className: "fa fa-envelope-o"}), "Email: ", prospect.email), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Job:"), " ", prospect.current_job), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Location:"), " ", prospect.location), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Industry:"), " ", prospect.industry)
                ), 
                React.createElement("div", {className: "image"}, 
                    React.createElement("p", null, "Wealth Score"), 
                    React.createElement("h4", {className: "money"}, prospect.wealthscore)
                ), 
                React.createElement("div", {className: "buttons"}, 
                    React.createElement("a", {className: "add-prospect", "data-id": prospect.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-warning prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Change Status"))
                ), 
                React.createElement("div", {className: "clear"}), 
                React.createElement(SocialAccounts, {data: prospect.social_accounts})
            )
            )
    }
});


var ClientList = React.createClass({displayName: "ClientList",
    getInitialState: function() {
        return {data:[]};
    },
    componentDidMount: function() {
        setTimeout(this.loadInLinkedinScript, 1000);
    },
    loadInLinkedinScript: function() {
        IN.parse(document.body);
    },
    render: function() {
        var prospects = this.props.data.map(function(prospect) {

            return (
                React.createElement("div", {className: "prospect"}, 
                    React.createElement(Prospect, {data: prospect})
                )
                );
        });
        return (
          React.createElement("div", {"data-client-list": this.props.name, className: "results"}, 
            React.createElement("div", {className: "wrapper"}, 
                React.createElement("h2", {className: "leaders"}, "Date: ", React.createElement("span", {className: "green"}, this.props.name), " ", React.createElement("div", {className: "pull-right neg-top"}, React.createElement("button", {"data-export": this.props.name, className: "btn btn-success"}, "Export"))), 
                prospects, 
                React.createElement("div", {className: "clear"})
            )
          )
          )
    }
});

var ClientLists = React.createClass({displayName: "ClientLists",
    loadProfileFromServer: function() {
        $.ajax({
          url: "/api/clientlists",
          data:{p:page},
          dataType: 'json',
          success: function(data) {
            if (data.success.length < 1) {
                bootbox.alert("There are no results for this query");
            }
            this.setProps({data: data.success});
            bindProfiles();
            this.bindExport();
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
        this.loadProfileFromServer()
        this.bindExport();
    },
    loadInLinkedinScript: function() {
        IN.parse(document.body);
    },
    bindExport: function() {
        $("[data-export]").click(function(e) {
            var id = $(this).data("export");
            e.preventDefault();
            exportList(id);
        });
    },
    render: function() {
    var prospects = this.props.data.map(function(prospects) {
        return (
                React.createElement(ClientList, {name: prospects.name, data: prospects.data})
            );
    });
    if (this.props.data.length < 1) {
        return (
          React.createElement("div", {className: "results"}, 
            React.createElement("div", {className: "empty"}, 
                React.createElement("h2", null, "You have no clients saved yet")
            ), 

            React.createElement("div", {className: "clear"})
          )
        );
    } else {
        return (
          React.createElement("div", {className: "days"}, 
            prospects, 
            React.createElement("div", {className: "clear"})
          )
        );
    }
  }
});

function exportList(id) {
  var vals = []
  $("[data-client-list='" + id + "'] input:checked").each(function() {
      vals.push($(this).val())
  });
  var params={"ids": vals.join()}
  $.post("/export", params, function(data) {
      bootbox.alert("The export is being emailed to you");
  });
}


function buildResults() {


    var searchData = []
    React.render(
        React.createElement(ClientLists, {data: searchData}),
        document.getElementById('clients')
    );
}


$(function() {
    buildResults();
    bindProfiles();
});

function bindProfiles() {
    $("[data-prospect]").click(function() {
        var url = $(this).data('url');
        var id = $(this).data("prospect");
        loadProfile(id, url);
    });
}

