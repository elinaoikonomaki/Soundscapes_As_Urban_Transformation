// FINAL Project 6.859 -- Elina Oikonomaki
//

// containins all of the timeline Elements
let timeLineSVGDocument;
// the JSON-Object
let dayJSONObj;

// current Walks Json;
let currentWalksJSONObj = {};
var sketchWidth;
var sketchHeight;
let geoJSON;
var allPoints = {};
let mappa;

var objCalls = 0;

// the colors
let clsFaded;
let cls;
let BACKGROUND_CLR;

let boxesClickedIdx = 0;

// interaction of map
var mapInteractionLn;
var mapInteractionIdx;

// the current soundURL
var currSound;
var currSoundTimeStmp;
var soundStop = true;
var currSoundTime; // the current timestamp of the audio track when playing
var soundInteractionIdx;
var currSoundSemantic;
var currSoundAanalytic;

// semantic segmentation class map json
var semanticClasses;

// street/building status
var bbStatus = {};
var bstStatus = {};
var bstOrStatus = {};

// vertex
//
var currVertex = [];


/// TEST
var namedict;

var phaseColors;



// some p5 to load the local JSON as object
function setup() {

    BACKGROUND_CLR = color(255, 255, 255);
    // colors for the line
    clsFaded = [color(171, 0, 105, 100), color(145, 50, 209, 100), color(0, 59, 177, 100), color(171, 115, 0, 100), color(183, 202, 81, 100), color(0, 149, 0, 100), color(57, 67, 90, 100)];
    cls = [color(171, 0, 105), color(145, 50, 209), color(0, 59, 177), color(171, 115, 0), color(183, 202, 81), color(0, 149, 0), color(57, 67, 90)];


    clsFaded = [color(0, 0, 0, 100), color(0, 0, 0, 100), color(0, 0, 0, 100), color(0, 0, 0, 100), color(0, 0, 0, 100), color(0, 0, 0, 100), color(0, 0, 0, 100)];

    cls = [color(0, 0, 0), color(0, 0, 0), color(0, 0, 0), color(0, 0, 0), color(0, 0, 0), color(0, 0, 0), color(0, 0, 0)];



    function getRandomInt(max) {
        return Math.floor(Math.random() * max);
    }


    // colors by clusters not phases
    phaseColors = {
        '0': [38, 115, 101],
        '1': [242, 203, 5],
        '2': [242, 159, 5],
        '3': [242, 135, 5],
        '4': [242, 48, 48]
    };

    phaseColors = {}

    for (let step = -1; step < 500; step++) {
        phaseColors[step.toString()] = [240, 240, 240];
    }

    // add the clusternames you want to be displayed
    phaseColors["-1"] = [240, 240, 240];
    phaseColors["14"] = [161, 71, 82];
    phaseColors["30"] = [221, 218, 178];
    phaseColors["22"] = [99, 90, 191];
    phaseColors["21"] = [164, 186, 184];
    phaseColors["0"] = [142, 158, 158];
    phaseColors["3"] = [204, 178, 143];
    phaseColors["9"] = [94, 105, 105];
    phaseColors["15"] = [204, 178, 143];
    phaseColors["7"] = [191, 117, 150];
    phaseColors["6"] = [157, 204, 203];
    phaseColors["41"] = [122, 135, 135];
    phaseColors["17"] = [161, 71, 82];
    phaseColors["10"] = [161, 71, 82];
    phaseColors["12"] = [161, 71, 82];


    semanticClasses = loadJSON("/data/yamnet_class_map.json");
    dayJSONObj = loadJSON("/data/activedays.json");
    sketchWidth = document.getElementById("p5-sketch-Container").offsetWidth;
    sketchHeight = document.getElementById("p5-sketch-Container").offsetHeight;

    var canvas = createCanvas(sketchWidth, sketchHeight);
    canvas.parent('p5-sketch-Container');
}


function mousePressed() {
    console.log(bbStatus);
}


// poitns of interest
var poi = {};

function draw() {

    background(BACKGROUND_CLR);
    // cumulative duration of all points
    var all_ln_glob_x = [];
    var tracks = Object.keys(allPoints).length;

    if (tracks > 0) {
        var i = 0;
        for (var j = 0; j < tracks; j++) {
            bbStatus[j] = [];
        }
        for (let walkIdx in allPoints) {
            poi[i] = {};
            for (let ptIdx in allPoints[walkIdx]) {

                stroke(0); //Coloring lines stroke(clsFaded[i]);
                line(all_ln_glob_x[i], i * height / tracks + height / tracks / 6, all_ln_glob_x[i], (i + 1) * height / tracks - (height / tracks) / 2) - 40; //+-6


                // on mouse interaction we highlight the corresponding line
                if (mapInteractionLn) {
                    push();
                    strokeWeight(3);
                    if (boxesClickedIdx - 1 == i) {
                        line(mapInteractionLn, i * height / tracks, mapInteractionLn, (i + 1) * height / tracks) - 40; //+-6
                    }
                    pop();
                }

                // check if the soundURL is not empty
                push();
                if (currSoundTime) {
                    var semanticH = 0;
                    if (boxesClickedIdx - 1 == i) {
                        fill('red');
                        if (currSoundTime % 2 == 0) {
                            noFill();
                        }
                        stroke('red');
                        ellipse(mapInteractionLn + 10 + currSoundTime, (i + 1) * height / tracks - 10, 10, 10);
                        line(mapInteractionLn + currSoundTime, i * height / tracks + 10, mapInteractionLn + currSoundTime, (i + 1) * height / tracks) - 20;
                        noStroke();
                        fill('red');

                        text('CH1:', mapInteractionLn + 10 + currSoundTime, (i + 1) * height / tracks - 50 + semanticH);
                        Object.entries(currSoundSemantic[0][currSoundTime]).forEach(([k, v]) => {
                            text(semanticClasses[k] + ":   " + v, mapInteractionLn + 10 + currSoundTime, (i + 1) * height / tracks - 40 + semanticH);
                            semanticH += 10;
                        });

                        text('CH2:', mapInteractionLn + 10 + currSoundTime, (i + 1) * height / tracks - 130 + semanticH);
                        Object.entries(currSoundSemantic[1][currSoundTime]).forEach(([k, v]) => {
                            text(semanticClasses[k] + ":   " + v, mapInteractionLn + 10 + currSoundTime, (i + 1) * height / tracks - 120 + semanticH);
                            semanticH += 10;
                        });
                    }
                }
                pop();

                //var analytic = allPoints[walkIdx][ptIdx]['geoPt']['properties']['sound']['analytic'];
                // tt -> x axis
                // t -> y axis
                var distr = allPoints[walkIdx][ptIdx]['geoPt']['properties']["distribution"];

                push();
                const change_t_avg = change_t => change_t.reduce((a, b) => a + b, 0) / change_t.length;

                var x_1 = all_ln_glob_x[i];
                var x_1_n = all_ln_glob_x[i] + allPoints[walkIdx][ptIdx].duration * (width / 1650);

                var x_2 = all_ln_glob_x[i];
                var x_2_n = all_ln_glob_x[i + 1];

                var y_1 = (i + 1) * height / tracks - (height / tracks) / 2;
                var y_2 = (i + 1) * height / tracks - height / tracks / 6;

                var abs_dist = y_2 - y_1;
                // loopint through the distribution values
                var toplineYval = y_1;
                for (const [key, value] of Object.entries(distr)) {

                    fill_trans = 255;
                    if (mouseX > x_1 && mouseX < x_1_n && mouseY > toplineYval && mouseY < toplineYval + abs_dist * value) {
                        fill_trans = 50;
                        push();
                        stroke(255);
                        textSize(14);
                        fill(cls[i]);
                        text("Cluster: " + key, mouseX, (i + 1) * height / tracks - 18);
                        text("Percentage: " + value, mouseX, (i + 1) * height / tracks);
                        strokeWeight(3);
                        stroke(cls[i]);
                        pop();
                    }

                    var idx = parseInt(key);
                    var rgbCols = phaseColors[idx];

                    noStroke();

                    fill(rgbCols[0], rgbCols[1], rgbCols[2], fill_trans);

                    beginShape();
                    // top of the line is y_1 value
                    vertex(x_1, toplineYval);
                    vertex(x_2, toplineYval + abs_dist * value);
                    vertex(x_1_n, toplineYval + abs_dist * value);
                    vertex(x_1_n, toplineYval);
                    endShape();



                    toplineYval += abs_dist * value;
                }

                // for (var c = 0; c < change_t.length; c++) {
                // line(all_ln_glob_x[i], (i + 1) * height / tracks - (height / tracks) / 2 - map(change_t[c] / 4, 0, 200, 0, (height / tracks) * 1.5), all_ln_glob_x[i], (i + 1) * height / tracks - (height / tracks) / 2 + map(change_t[c] / 4, 0, 200, 0, (height / tracks) * 1.5));
                // }

                pop();

                push();
                textSize(8);
                noStroke();
                noFill();
                translate(all_ln_glob_x[i], i * height / tracks);


                var properties = allPoints[walkIdx][ptIdx]['geoPt']['properties'];


                // here we add the place Status Lines
                // bb = boundary boulding -  1 => change
                // bb = boundary building - 0 => no change
                // bst = boundary street = - 1, 0
                // bst_or = boundary street orientation - Left , Right (Top/Bottom)
                //

                rotate(radians(45));
                fill(cls[i]);

                if (properties['placeloc']) {
                    // update the current one
                    //
                    var phase = properties['placeloc'];
                    //
                    var bb = phase['bb'];
                    var bst = phase['bst'];
                    var bb_or = phase['bb_or'];
                    var bst_or = phase['bst_or'];
                    var name = phase['name'];

                    var nm1 = { 'bb': bb, 'bst': bst, 'bb_or': bb_or, 'bst_or': bst_or };
                    var namedict = {};
                    namedict[name] = nm1;

                    // TODO fix this
                    if (name != 'Big Picture Framing-Harvard Square' && name != 'Karma Yoga Studio & Karma Gym') {
                        bbStatus[i].push(namedict);
                    }

                    // we add the points of interest
                    poi[i][properties['placeloc']['name']] = all_ln_glob_x[i];
                    stroke(clsFaded[i]);
                    noFill();
                    // if the shop is open we fill otherwise not
                    if (phase['status'] == "Open") { fill(cls[i]); }
                    //mouseOver Triangle
                    triangle(0, 0, -5, 5, 5, 5);
                    if (mouseX > all_ln_glob_x[i] - 2 && mouseY > i * height / tracks + 6 && mouseX < all_ln_glob_x[i] + 2 && mouseY < (i + 1) * height / tracks) {
                        noStroke();
                        textSize(12);
                        fill(cls[i]);
                        text(phase['name'], 20, 8);
                        strokeWeight(3);
                        stroke(cls[i]);
                    }
                    push();
                    rotate(radians(-45));
                    line(0, 0 + 10, 0, (i + 1) * height / tracks) - 10;
                    pop();
                }
                pop();

                // the 5 is the distance we need to change
                if (!all_ln_glob_x[i]) {
                    all_ln_glob_x[i] = 0;
                }
                all_ln_glob_x[i] += allPoints[walkIdx][ptIdx].duration * (width / 1650);
                allPoints[walkIdx][ptIdx].globX = all_ln_glob_x[i];
            }
            i++;
        }


        // Yellow overlay for mousOver same places
        var i = 0;
        var poi_name;
        for (let tr in poi) {
            for (let nm in poi[tr]) {
                var curr_x = poi[tr][nm];

                if (mouseX > curr_x - 2 && mouseY > i * height / tracks + 6 && mouseX < curr_x + 2 && mouseY < (i + 1) * height / tracks) {
                    lnSgm = []
                    for (var j = 0; j < tracks; j++) {
                        lnSgm.push([poi[j][nm], j * height / tracks]);
                    }
                    if (lnSgm.length > 1) {
                        push();
                        stroke('black');
                        strokeWeight(3);
                        beginShape();

                        noFill();
                        for (var k = 0; k < lnSgm.length; k++) {

                            vertex(lnSgm[k][0], lnSgm[k][1]);
                            vertex(lnSgm[k][0], (k + 1) * height / tracks);
                        }
                        endShape();
                        pop();
                    }
                } else {
                    poi_name = null;
                }
            }
            i++;
        }

        // left BB
        var i = 0;

        for (let tr in poi) {
            push();
            strokeWeight(3);
            stroke(cls[i]);
            noFill();
            beginShape();
            for (let nm in poi[tr]) {
                var curr_x = poi[tr][nm];
                // the boarder/street status
                for (var j = 0; j < bbStatus[i].length; j++) {
                    var curr_poi = bbStatus[i][j][nm];
                    if (curr_poi) {

                        // the left Building
                        if (curr_poi['bb'] == 1 && curr_poi['bb_or'] == 'L') {
                            vertex(curr_x - 5, i * height / tracks + height / tracks * 0.13);
                            endShape();

                            beginShape();
                            vertex(curr_x - 5, i * height / tracks + height / tracks * 0.1);
                            vertex(curr_x + 5, i * height / tracks + height / tracks * 0.1);
                            endShape();

                            beginShape();
                            vertex(curr_x + 5, i * height / tracks + height / tracks * 0.13);
                        } else if (curr_poi['bb'] == 0 && curr_poi['bb_or'] == 'L') {
                            vertex(curr_x, i * height / tracks + height / tracks * 0.13);
                        }

                    }

                }

            }
            endShape();
            i++;
            pop();
        }


        var i = 0;
        // left BST
        for (let tr in poi) {
            push();
            strokeWeight(1);
            stroke(cls[i]);
            noFill();
            beginShape();
            for (let nm in poi[tr]) {
                var curr_x = poi[tr][nm];
                // the boarder/street status
                for (var j = 0; j < bbStatus[i].length; j++) {
                    var curr_poi = bbStatus[i][j][nm];
                    if (curr_poi) {

                        // the left Building
                        if (curr_poi['bst'] == 1 && curr_poi['bst_or'] == 'L') {
                            vertex(curr_x - 5, i * height / tracks + height / tracks * 0.13);

                            vertex(curr_x - 5, i * height / tracks + height / tracks * 0.1);
                            vertex(curr_x + 5, i * height / tracks + height / tracks * 0.1);

                            vertex(curr_x + 5, i * height / tracks + height / tracks * 0.13);
                        } else if (curr_poi['bb'] == 0 && curr_poi['bb_or'] == 'L') {
                            vertex(curr_x, i * height / tracks + height / tracks * 0.13);
                        }

                    }

                }

            }
            endShape();
            i++;
            pop();
        }

        // right BB
        var i = 0;
        for (let tr in poi) {
            push();
            strokeWeight(3);
            stroke(cls[i]);
            noFill();
            beginShape();
            for (let nm in poi[tr]) {
                var curr_x = poi[tr][nm];
                // the boarder/street status
                for (var j = 0; j < bbStatus[i].length; j++) {
                    var curr_poi = bbStatus[i][j][nm];
                    if (curr_poi) {

                        // the left
                        if (curr_poi['bb'] == 1 && curr_poi['bb_or'] == 'R') {
                            vertex(curr_x + 5, (i + 1) * height / tracks - height / tracks * 0.13);
                            endShape();

                            beginShape();
                            vertex(curr_x + 5, (i + 1) * height / tracks - height / tracks * 0.1);
                            vertex(curr_x - 5, (i + 1) * height / tracks - height / tracks * 0.1);
                            endShape();

                            beginShape();
                            vertex(curr_x - 5, (i + 1) * height / tracks - height / tracks * 0.13);
                        } else if (curr_poi['bb'] == 0 && curr_poi['bb_or'] == 'R') {
                            vertex(curr_x, (i + 1) * height / tracks - height / tracks * 0.13);
                        }
                    }

                }

            }
            endShape();
            i++;
            pop();
        }

        // right BB
        var i = 0;
        for (let tr in poi) {
            push();
            strokeWeight(1);
            stroke(cls[i]);
            noFill();
            beginShape();
            for (let nm in poi[tr]) {
                var curr_x = poi[tr][nm];
                // the boarder/street status
                for (var j = 0; j < bbStatus[i].length; j++) {
                    var curr_poi = bbStatus[i][j][nm];
                    if (curr_poi) {

                        // the left
                        if (curr_poi['bst'] == 1 && curr_poi['bst_or'] == 'R') {
                            vertex(curr_x + 5, (i + 1) * height / tracks - height / tracks * 0.13);

                            vertex(curr_x + 5, (i + 1) * height / tracks - height / tracks * 0.1);
                            vertex(curr_x - 5, (i + 1) * height / tracks - height / tracks * 0.1);

                            vertex(curr_x - 5, (i + 1) * height / tracks - height / tracks * 0.13);
                        } else if (curr_poi['bb'] == 0 && curr_poi['bb_or'] == 'R') {
                            vertex(curr_x, (i + 1) * height / tracks - height / tracks * 0.13);
                        }
                    }

                }

            }
            endShape();
            i++;
            pop();
        }

    }
}


function windowResized() {
    sketchWidth = document.getElementById("p5-sketch-Container").offsetWidth;
    sketchHeight = document.getElementById("p5-sketch-Container").offsetHeight;
    resizeCanvas(sketchWidth, sketchHeight);
}

// var newurl = "https://dl.dropboxusercontent.com/s/d0xsijpf5v8g97a/08012020_PM.json?raw=1";
// -------- DOM Events
document.addEventListener('DOMContentLoaded', function() {
    //Fires after the html has loaded    
    assignTimeLineButtonActivity();



});

// --------- 1. DOMCONTENTLOADED DOM FUNCTIONS
// --------- Contains all the functions that are called in the DOMContentLoaded EL.
function assignTimeLineButtonActivity() {

    // we load the JSON
    // we get the SVG
    var tmlsvg = document.getElementById("timelineSVG");

    // we wait until the SVG is loaded then we get the document
    tmlsvg.addEventListener('load', function() {
        timeLineSVGDocument = tmlsvg.contentDocument;

        // we create
        var linkElm = timeLineSVGDocument.createElementNS("http://www.w3.org/1999/xhtml", "link");
        linkElm.setAttribute("href", "../style.css");
        linkElm.setAttribute("type", "text/css");
        linkElm.setAttribute("rel", "stylesheet");

        // css injection
        $("svg", timeLineSVGDocument).first().prepend(linkElm);
        // remove inline css 
        $("style", timeLineSVGDocument).remove();

        // AM AND PM
        var timelineBoxesPM = $("[id*='_PM']", timeLineSVGDocument)
        var timelineBoxesAM = $("[id*='_AM']", timeLineSVGDocument)

        // THE AM BOXES
        timelineBoxesAM.each(function() {
            // cleaning up the id
            var replaceId = $(this)[0].id.replace('_x3', '').replace('_', '').replace('_x5F', '');
            $(this).attr('id', replaceId);
            // adding an additional Color
            $(this).addClass('timelineBoxAMDefault');

            // EventListener for Morning Boxes
            $(this).on("mouseover", function() {
                if (!$(this).hasClass('timelineBoxAMSelected')) {
                    $(this).addClass('timelineBoxAMActive').removeClass('timelineBoxAMDefault');
                    // nested svg
                    //console.log($("#timeLineButtonDeselectAll",timeLineSVGDocument));
                    // external svg
                    //console.log($("#photoSVGContainer",document));
                }
            });

            $(this).on("mouseleave", function() {
                if (!$(this).hasClass('timelineBoxAMSelected')) {
                    $(this).removeClass('timelineBoxAMActive').addClass('timelineBoxAMDefault');
                }
            });

            //Loading JSON files on click //

            $(this).on("click", function(e) {
                if (!$(this).hasClass('timelineBoxAMSelected')) {
                    $(this).removeClass('timelineBoxAMActive').removeClass('timelineBoxAMDefault').addClass('timelineBoxAMSelected');
                    // we retrieve the right json for this element

                    $(this).attr("fill", cls[boxesClickedIdx].toString('rgb'));
                    boxesClickedIdx += 1;

                    var dayVal = dayJSONObj.days[$(this).attr('id')];
                    // if the url is not null we set the current walk to
                    if (dayVal.url != "") {
                        updateCurrentWalkJSON(dayVal.url, $(this).attr('id'))
                    }

                    // this waits for the variable to be be true until then it does nothing
                    (async() => {
                        while (!currentWalksJSONObj.hasOwnProperty($(this).attr('id'))) // define the condition as you like
                            await new Promise(resolve => setTimeout(resolve, 1000));
                        console.log("AM");
                        createDurationPath(this.id);
                        createMapPts();

                    })();
                } else {
                    $(this).removeClass('timelineBoxAMSelected');
                    // remove the data from the walk again
                    delete currentWalksJSONObj[$(this).attr('id')];
                    // remove the amount of boxes
                    boxesClickedIdx -= 1;
                    $(this).removeAttr("fill");
                    // delete horizontal lines
                    // $("[id*='_linearPath']", document).remove();
                }

            });
        });

        // THE PM BOXES
        timelineBoxesPM.each(function() {
            // cleaning up the id
            var replaceId = $(this)[0].id.replace('_x3', '').replace('_', '').replace('_x5F', '');
            $(this).attr('id', replaceId);
            // adding an additional Color
            $(this).addClass('timelineBoxPMDefault');

            // EventListener for Morning Boxes
            $(this).on("mouseover", function() {
                if (!$(this).hasClass('timelineBoxPMSelected')) {
                    $(this).addClass('timelineBoxPMActive').removeClass('timelineBoxPMDefault');
                }
            });

            $(this).on("mouseleave", function() {
                if (!$(this).hasClass('timelineBoxPMSelected')) {
                    $(this).removeClass('timelineBoxPMActive').addClass('timelineBoxPMDefault');
                }
            });


            $(this).on("click", function(e) {

                if (!$(this).hasClass('timelineBoxPMSelected')) {
                    $(this).removeClass('timelineBoxPMActive').removeClass('timelineBoxPMDefault').addClass('timelineBoxPMSelected');

                    $(this).attr("fill", cls[boxesClickedIdx].toString('rgb'));
                    boxesClickedIdx += 1;

                    // we retrieve the right json for this element
                    var dayVal = dayJSONObj.days[$(this).attr('id')];
                    // if the url is not null we set the current walk to
                    if (dayVal.url != "") {
                        updateCurrentWalkJSON(dayVal.url, $(this).attr('id'))
                    }

                    // this waits for the variable to be be true until then it does nothing
                    (async() => {
                        while (!currentWalksJSONObj.hasOwnProperty($(this).attr('id'))) // define the condition as you like
                            await new Promise(resolve => setTimeout(resolve, 1000));

                        createDurationPath(this.id);
                        createMapPts();



                        // createPath();
                    })();

                } else {
                    $(this).removeClass('timelineBoxPMSelected');
                    // remove the data from the walk again
                    delete currentWalksJSONObj[$(this).attr('id')];


                    boxesClickedIdx -= 1;

                    // delete horizontal lines
                    $("[id*='_linearPath']", document).remove();

                    // horElemC = 0;
                }

            });
        });

        // THE DESELECT ALL ELEMENTS BUTTON
        $('#timeLineButtonDeselectAll', timeLineSVGDocument).each(function() {
            $(this).on("click", function() {
                // remove selection
                $('.timelineBoxPMSelected', timeLineSVGDocument).removeClass('timelineBoxPMSelected').addClass('timelineBoxPMDefault');
                $('.timelineBoxAMSelected', timeLineSVGDocument).removeClass('timelineBoxAMSelected').addClass('timelineBoxAMDefault');
                // delete horizontal lines  
                $("[id*='_linearPath']", document).remove();
                horElemC = 0;
                allPoints = {};
                boxesClickedIdx = 0;

                mapInteractionLn = null;

                //reset walks
                currentWalksJSONObj = {};
            });
        });
    });
}


//

function createDurationPath(timeId) {
    var calls = 0;
    for (let currObj in currentWalksJSONObj) {
        // console.log(Object.keys(currentWalksJSONObj));
        // console.log(currentWalksJSONObj[currObj].features);
        tmpPt = [];


        currentWalksJSONObj[currObj].features.forEach(function(point) {
            var colorShade = map(point.properties.duration, 0, 40, 0, 255);
            var currPt = new gpsPoint(point, point.properties.duration, colorShade);
            currPt.colorShade = colorShade;
            tmpPt.push(currPt);
        });
        allPoints[timeId] = tmpPt;
        // console.log(allPoints);           
    }
};



function gpsPoint(geoPt, duration, colorShade) {
    this.geoPt = geoPt;
    this.duration = duration;
    this.colorShade = colorShade;
    this.globX = '';
}

// --------- REQUEST UTILS

function updateCurrentWalkJSON(url, callerId) {

    /*
     * returns async json from DROPBOX
     * Needs to have the format: https://dl.dropboxusercontent.com/s/myjsonhash.json?raw=1
     */

    async function fetchDropboxJSON(urlA) {
        let response = await fetch(url, {
            method: 'GET',
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin',
            headers: {},
            referrer: 'no-referrer',
        })
        let data = await response.json()
        return data;
    };

    async function main() {
        currentWalksJSONObj[callerId] = await fetchDropboxJSON(url);
    }
    main();
}


// --------- SVG UTILS

function dayBoxAddEventListener(svgElem) {
    /* 
     * Event Listeners for svg day boxes
     */

    // when the mouse enters the line
    svgElem.addEventListener("mouseenter", function(event) {
        // focus the mouseenter target
        svgElem.clssList.add('lineHi');
        svgElem.classList.remove('lineClick');
        //svgC.appendChild(svgElem);
    }, false);

    // when the mouse leaves the line
    svgElem.addEventListener("mouseleave", function(event) {
        // unfocus the mouseleave target
        svgElem.classList.remove('lineUp');
        svgElem.classList.remove('lineHi');
    }, false);

    // when the mouse clicks the line
    // https://css-tricks.com/svg-line-animation-works/
    svgElem.addEventListener("click", function(event) {
        console.log("mouse clicking: " + event.target.id);
    }, false);
}


//Mapbox
//Elina's access token 



function createMapPts() {
    var calls = 0;
    var song;
    var currMap;

    for (let currObj in currentWalksJSONObj) {
        currMap = currentWalksJSONObj[currObj];
    }

    mapboxgl.accessToken = 'pk.eyJ1IjoiZWxpbmFvaWsiLCJhIjoiY2tidWwzenhvMDVyMTJ4bzVyYWVlMGdkZSJ9.ZzKoxiO3-YaCk4CJilMPVA';

    mappa = new mapboxgl.Map({
        container: 'mapboxContainer', // container id
        style: 'mapbox://styles/elinaoik/ckov2hlfu7c1517mdfm2qx7zq', // style URL
        center: [-71.115, 42.372], // starting position [lng, lat]
        zoom: 15.26 // starting zoom
    });

    mappa.addControl(new mapboxgl.NavigationControl());

    mappa.on('load', function() {
        mappa.addSource('currMap', currMap);

        mappa.addLayer({
            'id': 'currMap',
            'type': 'circle',
            'source': 'currMap',
            'paint': {
                'circle-color': cls[boxesClickedIdx - 1].toString('rgb'),
                'circle-opacity': 0.5,
                'circle-radius': ['get', 'duration']
            }
        });

        // Create a popup, but don't add it to the map yet.
        /*
        var popup = new mapboxgl.Popup({
            className: "currWalk-popup",
            closeButton: true,
            closeOnClick: true,
        }).setMaxWidth(600);
        */

        mappa.on('mouseenter', 'currMap', function(e) {
            // Change the cursor style as a UI indicator.
            mappa.getCanvas().style.cursor = 'pointer';

            var coordinates = e.features[0].geometry.coordinates.slice();
            //console.log(time);
            var duration = e.features[0].properties.duration;

            //date modifications
            var time = new Date(e.features[0].properties.time);
            var month = time.getMonth() + 1;
            month = month.toString();
            if (month.length == 1) {
                month = '0' + month;
            }
            var date = time.getDate().toString();
            if (date.length == 1) {
                date = '0' + date;
            }
            var abbrTm = month + date + time.getFullYear().toString();
            if (time.getHours() > 17) {
                abbrTm += '_PM';
            } else { abbrTm += '_AM'; }

            // we loop to find the matching coordinates
            allPoints[abbrTm].forEach(function(entry) {

                var lat = entry.geoPt.geometry.coordinates[0];
                var lon = entry.geoPt.geometry.coordinates[1];
                var nlat = coordinates[0].toFixed(6);
                var nlon = coordinates[1].toFixed(6);
                if (lat == nlat && lon == nlon) {
                    // we set the active line
                    mapInteractionLn = entry.globX;
                }
            });


            // '<audio controls><source src="'+sound'+" type="audio/mp3"></audio>'

            var d_time = "<h2 style='color:red;'>" + time + "</h2>";
            var d_duration = "<div class=duration>duration: " + duration + "</div>";
            // var d_description = "<div>description: " + description + "</div>";
            var d_coordinates = "<div>coordinates: " + coordinates + "</div>";

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
            }

            // Populate the popup and set its coordinates
            // based on the feature found.
            //popup.setLngLat(coordinates).setHTML(d_time+d_duration).addTo(mappa);                                                                                                                                       
        });

        mappa.on('click', 'currMap', function(e) {


            var coordinates = e.features[0].geometry.coordinates.slice();

            // Change the cursor style as a UI indicator.
            mappa.getCanvas().style.cursor = 'pointer';

            //date modifications
            var time = new Date(e.features[0].properties.time);
            var month = time.getMonth() + 1;
            month = month.toString();
            if (month.length == 1) {
                month = '0' + month;
            }
            var date = time.getDate().toString();
            if (date.length == 1) {
                date = '0' + date;
            }
            var abbrTm = month + date + time.getFullYear().toString();
            if (time.getHours() > 17) {
                abbrTm += '_PM';
            } else { abbrTm += '_AM'; }


            // we loop to find the matching coordinates
            allPoints[abbrTm].forEach(function(entry) {

                var lat = entry.geoPt.geometry.coordinates[0];
                var lon = entry.geoPt.geometry.coordinates[1];
                var nlat = coordinates[0].toFixed(6);
                var nlon = coordinates[1].toFixed(6);

                if (lat == nlat && lon == nlon) {

                    soundInteractionIdx = abbrTm;

                    currSoundSemantic = entry.geoPt.properties.sound.semantic;
                    currSoundAanalytic = entry.geoPt.properties.sound.analytic;

                    // we load the audio
                    currSound = new Audio(entry.geoPt.properties.sound.url);
                    currSound.load();

                    currSound.addEventListener('timeupdate', () => {
                        currSoundTime = Math.floor(currSound.currentTime);
                    });

                    currSound.addEventListener('ended', (event) => {
                        currSoundTime = null;
                    });

                    currSound.addEventListener('canplaythrough', () => {
                        // The duration variable now holds the duration (in seconds) of the audio clip
                        console.log(entry.geoPt.properties.sound.url);
                        currSound.play();
                    });

                } else {}

            });



            // var coordinates = e.features[0].geometry.coordinates.slice();
            // console.log("coordinates");
            // var time = e.features[0].properties.time;
            //
            //var SoundUl = e.properties['sound'].url;
            //console.log(SoundUl);
            //console.log(currMap);
            // var duration = e.features[0].properties.duration;

            // console.log(currMap);

            //   var s = e.features[0].properties;
            //   console.log(s);
            // for (var i=0; i<s.length; i++){
            //   console.log(s[0]);
            // }

            // var sound = e.features[0].properties.sound.url;
            // var song = loadSound(sound);
            // song.play();
        });

        mappa.on('mouseleave', 'currMap', function(e) {
            mappa.getCanvas().style.cursor = '';
            //popup.remove();
            // we remove the interactivity
            mapInteractionLn = null;
            currSoundURL = null;
            soundStop = true;
            // var sound = e.features[0].properties.sound.url;
            // var song = loadSound(sound);
            // song.pause();
        });

    });


};

// p1.bindPopup('<h3>transformation Phase 1</h3><p>June 7th-8th</p><img src="../img/7th/IMG_0955.jpeg" style="width: 50%"> <img src="../img/8th/Frame-25-06-2020-09-26-55.jpeg" style="width: 50%"> <video width="320" height="240" controls><source src="movie.mp4" type="video/mp4"> <source src="movie.ogg" type="video/ogg">Your browser does not support the video tag.</video> <audio controls><source src="horse.ogg" type="audio/ogg"> <source src="horse.mp3" type="audio/mpeg">Your browser does not support the audio element.</audio> <audio controls><source src="horse.ogg" type="audio/ogg"><source src="horse.mp3" type="audio/mpeg">Your browser does not support the audio element.</audio>',{maxWidth:500,maxZoom:10});