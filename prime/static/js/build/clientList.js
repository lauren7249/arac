var industries = {}
var page = 1;

var Relationship = React.createClass({displayName: "Relationship",
    render: function() {
        return (
            React.createElement("p", null, "You are connected via ", React.createElement("a", {href: this.props.url}, this.props.name), ".")
            )
    }
});


var Prospect = React.createClass({displayName: "Prospect",
    render: function() {
        var prospect = this.props.data;
        var relationship = React.createElement(Relationship, {name: prospect.relevancy})
        return (
            React.createElement("div", {className: "result", "data-result": prospect.id}, 
                React.createElement("div", {className: "first"}
                ), 
                React.createElement("div", {className: "second"}, 
                    React.createElement("h3", null, React.createElement("a", {"data-prospect": prospect.id, "data-url": prospect.url}, prospect.name)), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Job:"), " ", prospect.current_job), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Location:"), " ", prospect.location), 
                    React.createElement("h4", null, React.createElement("span", {className: "grey"}, "Current Industry:"), " ", prospect.industry)
                ), 
                React.createElement("div", {className: "image"}, 
                    React.createElement("img", {src: prospect.image_url})
                ), 
                React.createElement("div", {className: "connections"}, 
                    React.createElement("h5", null, "Connection Path"), 
                    relationship
                ), 
                React.createElement("div", {className: "buttons"}, 
                    React.createElement("a", {className: "add-prospect", "data-id": prospect.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-success prospect-add"}, React.createElement("i", {className: "fa fa-plus"}), " Add To Prospect List")), 
                    React.createElement("a", {className: "remove-prospect", "data-id": prospect.id, href: "javascript:;"}, React.createElement("button", {className: "btn btn-danger"}, React.createElement("i", {className: "fa fa-chevron-circle-right"}), " Mark Prospect"))
                ), 
                React.createElement("div", {className: "clear"})
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
        this.bindButtons();
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
          React.createElement("div", {className: "results"}, 
            React.createElement("h2", null, this.props.name), 
            prospects, 
            React.createElement("div", {className: "clear"})
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
          }.bind(this),
          error: function(xhr, status, err) {
            console.log(err)
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
    },
    loadInLinkedinScript: function() {
        IN.parse(document.body);
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

