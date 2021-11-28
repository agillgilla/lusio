#define _GNU_SOURCE

#include <assert.h>
#include <ctype.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <math.h>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/statvfs.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <libavutil/mathematics.h>
#include <getopt.h>

#include "ilclient.h"

#include "log.h"
#include "text.h"

#include "imageLayer.h"

#include "bcm_host.h"

//-------------------------------------------------------------------------

#define NDEBUG

//-------------------------------------------------------------------------

uint8_t* g_canvas;
uint32_t g_canvas_size;
uint32_t g_canvas_width;
uint32_t g_canvas_height;

DISPMANX_MODEINFO_T info;

int startTimestampTextId;
int endTimestampTextId;

#define TIMESTAMP_PADDING 100
#define PROGRESS_PADDING 50

//-------------------------------------------------------------------------

#define DISP_CANVAS_BYTES_PER_PIXEL 4 // RGBA32 (RGBA8888)

void setStartTimestamp(const char *str, int strlen) {

    startTimestampTextId = createTextBitmap(str, strlen);

    text_set_text(startTimestampTextId, str, strlen);
    
    redraw_text(startTimestampTextId);
}

void setEndTimestamp(const char *str, int strlen) {

    endTimestampTextId = createTextBitmap(str, strlen);

    text_set_text(endTimestampTextId, str, strlen);
    
    redraw_text(endTimestampTextId);
}

int createTextBitmap(const char *str, int strlen)
{
    const char *font_file = "arial.ttf";
	
    // This comes out to a font size of 72 on a 1440p display
    int font_size = round(info.height / 20.0);
    
    printf("Font size: %d\n", font_size);

    return text_create(font_file, 0, font_size, 96);
}

void drawTextOverlay(int textId, uint32_t display, int32_t layer, IMAGE_LAYER_T *imageLayer, int32_t x, int32_t y, bool xFromRight, bool yFromBottom) {
    int textWidth;
    int textHeight;
    char *textBitmapData; 

    get_textdata(textId, &textWidth, &textHeight, &textBitmapData);

    initImageWithData(
        &(imageLayer->image),
        VC_IMAGE_RGBA32,
        textWidth,
        textHeight,
        false,
        textBitmapData);
    
    printf("Image dimensions: %dx%d\n", imageLayer->image.width, imageLayer->image.height);
    printf("Image aligned dimensions: %dx%d\n", imageLayer->image.pitch / (imageLayer->image.bitsPerPixel / 8), imageLayer->image.alignedHeight);   

    //---------------------------------------------------------------------

    createResourceImageLayer(imageLayer, layer);

    //---------------------------------------------------------------------

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);
    
    int computedX = x;
    int computedY = y;
    
    if (xFromRight) {
        computedX = x - imageLayer->image.width;
    }
    
    if (yFromBottom) {
        computedY = y - imageLayer->image.height;
    }

    addElementImageLayerOffset(imageLayer,
                               computedX,
                               computedY,
                               display,
                               update);

    int result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);
}

void getProgressBarInfo(int screenWidth, int screenHeight, IMAGE_LAYER_T *imageLayer, int *progressBarX, int *progressBarY,
                        int *progressBarWidth, int *progressBarHeight, int *progressOutlineThickness)
{
	 *progressBarWidth = round(screenWidth * 0.6);
    *progressBarHeight = round(screenHeight / 30.0);
    *progressOutlineThickness = round(*progressBarHeight / 5.0);
    *progressBarX = (screenWidth / 2) - (*progressBarWidth / 2);
    *progressBarY = screenHeight - imageLayer->image.height - (round(screenHeight * .042) - 10);//PROGRESS_PADDING;
}

void drawProgressBarOutline(uint32_t display, int32_t layer, IMAGE_LAYER_T *imageLayer, int screenWidth, int screenHeight)
{    
    int progressBarWidth;
    int progressBarHeight;
    int progressOutlineThickness;
    int progressBarX;
    int progressBarY;
    
    getProgressBarInfo(screenWidth, screenHeight, imageLayer, &progressBarX, &progressBarY, 
                       &progressBarWidth, &progressBarHeight, &progressOutlineThickness);
   
    int result = initImage(
        &(imageLayer->image),
        VC_IMAGE_RGBA32,
        progressBarWidth,
        progressBarHeight,
        false);
        
    RGBA8_T white = { 255, 255, 255, 255 };
    RGBA8_T black = { 0, 0, 0, 255 };
    
    for (int col = 0; col < progressBarWidth; col++) {
        for (int row = 0; row < progressBarHeight; row++) {
            
            if (col == 0 || col == (progressBarWidth - 1) || row == 0 || row == (progressBarHeight - 1)) {
                setPixelRGBA32(
                    &(imageLayer->image),
                    col,
                    row,
                    &black);
            }
            else if (col < progressOutlineThickness || 
                col >= progressBarWidth - progressOutlineThickness ||
                row < progressOutlineThickness ||
                row >= progressBarHeight - progressOutlineThickness) {

				    setPixelRGBA32(
                    &(imageLayer->image),
                    col,
                    row,
                    &white);
            }  
        }
    }
    
    //---------------------------------------------------------------------

    createResourceImageLayer(imageLayer, layer);

    //---------------------------------------------------------------------

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    addElementImageLayerOffset(imageLayer,
                               progressBarX,
                               progressBarY,
                               display,
                               update);

    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);
}

void drawProgressBarFill(uint32_t display, int32_t layer, IMAGE_LAYER_T *imageLayer, double percent, int screenWidth, int screenHeight)
{
    // Image layer was already initialized in drawProgressBarOutline(...)
    
    int progressBarWidth;
    int progressBarHeight;
    int progressOutlineThickness;
    int progressBarX;
    int progressBarY;
    
    getProgressBarInfo(screenWidth, screenHeight, imageLayer, &progressBarX, &progressBarY, 
                       &progressBarWidth, &progressBarHeight, &progressOutlineThickness);
    
    RGBA8_T white = { 255, 255, 255, 255 };
    
    for (int col = 0; col < progressBarWidth; col++) {
        for (int row = 0; row < progressBarHeight; row++) {
            
            if (col > 0 && col < progressBarWidth - 1 && row > 0 && row < progressBarHeight - 1) {
            	if (col < progressBarWidth * percent) {

				        setPixelRGBA32(
                        &(imageLayer->image),
                        col,
                        row,
                        &white);
                }  
            }
        }
    }
    
    //---------------------------------------------------------------------

    createResourceImageLayer(imageLayer, layer);

    //---------------------------------------------------------------------

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    addElementImageLayerOffset(imageLayer,
                               progressBarX,
                               progressBarY,
                               display,
                               update);

    int result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);
}

void drawProgressBar(uint32_t display, int32_t layer, IMAGE_LAYER_T *imageLayer, double percent, int screenWidth, int screenHeight)
{    
    drawProgressBarOutline(display, layer, imageLayer, screenWidth, screenHeight);
    
    // Always call drawProgressBarOutline BEFORE drawProgressBarFill!
    drawProgressBarFill(display, layer, imageLayer, percent, screenWidth, screenHeight);
}

void getStartAndEndTimestamps(int startSeconds, int endSeconds, char **startTimestamp, char **endTimestamp, int *startTimestampLen, int *endTimestampLen)
{	
    int endHours = endSeconds / (60 * 60);
    int remainEndSeconds = endSeconds % (60 * 60);
    int endMinutes = remainEndSeconds / 60;
    remainEndSeconds = endSeconds % 60;
    endSeconds = remainEndSeconds;
    
    int startHours = startSeconds / (60 * 60);
    int remainStartSeconds = startSeconds % (60 * 60);
    int startMinutes = remainStartSeconds / 60;
    remainStartSeconds = startSeconds % 60;
    startSeconds = remainStartSeconds;
    
    bool overHourLong = endHours > 0;
    
    if (overHourLong) {
        *endTimestamp = malloc(9 * sizeof(char));
        *endTimestampLen = sprintf(*endTimestamp, "%d:%02d:%02d", endHours, endMinutes, endSeconds);
        
        *startTimestamp = malloc(9 * sizeof(char));
        *startTimestampLen = sprintf(*startTimestamp, "%d:%02d:%02d", startHours, startMinutes, startSeconds);        
    } else {
        *endTimestamp = malloc(6 * sizeof(char));
        *endTimestampLen = sprintf(*endTimestamp, "%d:%02d", endMinutes, endSeconds);
        
        *startTimestamp = malloc(6 * sizeof(char));
        *startTimestampLen = sprintf(*startTimestamp, "%d:%02d", startMinutes, startSeconds);
    }
}

int main(int argc, char *argv[])
{
    int currSeconds;
    int totalSeconds;	
	
    if (argc < 3) {
        printf("overlay <current seconds> <total seconds>\n");
        exit(0);    
    } else {
        currSeconds = atoi(argv[1]);
        totalSeconds = atoi(argv[2]);
    }
	
	
    // Transparent (no) background.  Opaque black background causes graphics driver to crash?
    int32_t layer = 101;
    uint32_t displayNumber = 0;
    
    // Initialize text library   
    text_init();

    //---------------------------------------------------------------------   

    bcm_host_init();

    //---------------------------------------------------------------------

    DISPMANX_DISPLAY_HANDLE_T display = vc_dispmanx_display_open(displayNumber);
    assert(display != 0);

    //---------------------------------------------------------------------

    int result = vc_dispmanx_display_get_info(display, &info);
    assert(result == 0);
    

    //---------------------------------------------------------------------   
    
    g_canvas_width  = info.width;
    g_canvas_height = info.height;
    int pitch = g_canvas_width * DISP_CANVAS_BYTES_PER_PIXEL;
    g_canvas_size = pitch * g_canvas_height;
    g_canvas = calloc(1, g_canvas_size);
    assert(g_canvas);

    char *startTimestamp;
    char *endTimestamp;
    int startTimestampLen;
    int endTimestampLen;

    getStartAndEndTimestamps(currSeconds, totalSeconds, &startTimestamp, &endTimestamp, &startTimestampLen, &endTimestampLen);

    setStartTimestamp(startTimestamp, startTimestampLen);
    setEndTimestamp(endTimestamp, endTimestampLen);
    
    // Render all text bitmaps
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////// START TIMESTAMP //////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    IMAGE_LAYER_T startImageLayer;

    int startTextWidth;
    int startTextHeight;

    get_textsize(startTimestampTextId, &startTextWidth, &startTextHeight);

    drawTextOverlay(startTimestampTextId, display, layer, &startImageLayer, TIMESTAMP_PADDING, info.height, false, true);

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////// START TIMESTAMP //////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////// END TIMESTAMP ///////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    IMAGE_LAYER_T endImageLayer;

    int endTextWidth;
    int endTextHeight;

    get_textsize(endTimestampTextId, &endTextWidth, &endTextHeight);

    drawTextOverlay(endTimestampTextId, display, layer, &endImageLayer, info.width - TIMESTAMP_PADDING, info.height, true, true);

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////// END TIMESTAMP ///////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    IMAGE_LAYER_T progressImageLayer;
    
    drawProgressBar(display, layer, &progressImageLayer, ((double) currSeconds / (double) totalSeconds), info.width, info.height);

    //---------------------------------------------------------------------

    // Sleep for 10 milliseconds every run-loop
    const int sleepMilliseconds = 10;

    while (true)
    {
        usleep(sleepMilliseconds * 1000);
    }

    destroyImageLayer(&startImageLayer);
    destroyImageLayer(&endImageLayer);

    //---------------------------------------------------------------------

    result = vc_dispmanx_display_close(display);
    assert(result == 0);

    //---------------------------------------------------------------------

    return 0;
}

