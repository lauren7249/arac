var industries = {}
var page = 1;

var Relationship = React.createClass({
    render: function() {
        return (
            <p>You are connected via <a href={this.props.url}>{this.props.name}</a>.</p>
            )
    }
});

var SocialAccounts = React.createClass({
    getInitialState: function() {
        return {data:[]};
    },
    render: function() {
        var socialaccounts = this.props.data.map(function(account) {
            var name = "fa fa-" + account.type

            return (
                    <a href={account.url}><i className={name}></i> {account.typeName}</a>
                );
        });
        return (
            <div className='social'>
                <p><b>Social Accounts</b>:{socialaccounts}</p>
            </div>
            )
    }
});


var Prospect = React.createClass({
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
        var relationship = <Relationship name={prospect.relevancy} />
        return (
            <div className='result checked' data-result={prospect.id}>
                <div className='first'>
                    <input type='checkbox' value={prospect.id} defaultChecked={true} onChange={this.handleChange} />
                </div>
                <div className='second'>
                    <h3><a data-prospect={prospect.id} data-url={prospect.url}>{prospect.name}</a></h3>
                    <h4><i className='fa fa-envelope-o'></i> Email: {prospect.email}</h4>
                    <h4><span className='grey'>Current Job:</span> {prospect.current_job}</h4>
                    <h4><span className='grey'>Current Location:</span> {prospect.location}</h4>
                    <h4><span className='grey'>Current Industry:</span> {prospect.industry}</h4>
                    <SocialAccounts data={prospect.social_accounts} />
                </div>
                <div className='image'>
                    <p>Wealth Score</p>
                    <h4 className='money'>{prospect.wealthscore}</h4>
                </div>
                <div className='buttons'>
                    <a className='add-prospect' data-id={prospect.id} href='javascript:;'><button className='btn btn-warning prospect-add'><i className='fa fa-plus'></i> Change Status</button></a>
                </div>
                <div className='clear'></div>
            </div>
            )
    }
});


var ClientList = React.createClass({
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
                <div className='prospect'>
                    <Prospect data={prospect} />
                </div>
                );
        });
        return (
          <div data-client-list={this.props.name} className="results">
            <div className='wrapper'>
                <h2 className='leaders'>Date: <span className='green'>{this.props.name}</span> <div className='pull-right neg-top'><button data-export={this.props.name} className='btn btn-success'>Export</button></div></h2>
                {prospects}
                <div className='clear'></div>
            </div>
          </div>
          )
    }
});

var ClientLists = React.createClass({
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
                <ClientList name={prospects.name} data={prospects.data} />
            );
    });
    if (this.props.data.length < 1) {
        return (
          <div className="results">
            <div className='empty'>
                <h2>You have no clients saved yet</h2>
            </div>

            <div className='clear'></div>
          </div>
        );
    } else {
        return (
          <div className="days">
            {prospects}
            <div className='clear'></div>
          </div>
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
        <ClientLists data={searchData}  />,
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

