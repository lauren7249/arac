var industries = {}
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



function buildResults() {
    var searchData = []
    React.render(
        <Results data={searchData}  />,
        document.getElementById('prospects')
    );
}


$(function() {
    buildResults();
    bindSearch();
    bindDates();
});



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
