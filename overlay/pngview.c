//-------------------------------------------------------------------------
//
// The MIT License (MIT)
//
// Copyright (c) 2013 Andrew Duncan
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so, subject to
// the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
// CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
// TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//
//-------------------------------------------------------------------------

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

#include "backgroundLayer.h"
#include "imageLayer.h"

#include "bcm_host.h"

#include "loadpng.h"

//-------------------------------------------------------------------------

#define NDEBUG

//-------------------------------------------------------------------------

uint8_t* g_canvas;
uint32_t g_canvas_size;
uint32_t g_canvas_height;
uint32_t g_canvas_width;

int startTimestampTextId;
int endTimestampTextId;

#define TIMESTAMP_PADDING 100

//-------------------------------------------------------------------------

#define DISP_CANVAS_BYTES_PER_PIXEL 4 // RGBA32 (RGBA8888)

void set_start_timestamp(const char *str, int strlen) {

    startTimestampTextId = dispmanx_add_text(str, strlen);

    text_set_text(startTimestampTextId, str, strlen);
    
    redraw_text(startTimestampTextId);
}

void set_end_timestamp(const char *str, int strlen) {

    endTimestampTextId = dispmanx_add_text(str, strlen);

    text_set_text(endTimestampTextId, str, strlen);
    
    redraw_text(endTimestampTextId);
}

int dispmanx_add_text(const char *str, int strlen)
{
    const char *font_file = "arial.ttf";
	
    // This comes out to a font size of 80 on a 1440p display
    //int font_size = round(g_modeInfo.width / 30.0);
    int font_size = 72;
    
    printf("Font size: %d\n", font_size);

    return text_create(font_file, 0, font_size, 96);
}

int main(int argc, char *argv[])
{
    // Transparent (no) background.  Opaque black background causes graphics driver to crash?
    int32_t layer = 101;
    uint32_t displayNumber = 0;
    int32_t xOffset = 0;
    int32_t yOffset = 0;
    
    // initialize text library
    // TODO: Uncomment this!    
    text_init();

    //---------------------------------------------------------------------

    IMAGE_LAYER_T imageLayer;
    
    /*
    const char *imagePath = "/usr/share/icons/hicolor/512x512/mimetypes/application-x-bluefish-project.png";

    if(strcmp(imagePath, "-") == 0)
    {
        // Use stdin
        if (loadPngFile(&(imageLayer.image), stdin) == false)
        {
            fprintf(stderr, "unable to load %s\n", imagePath);
            exit(EXIT_FAILURE);
        }
    }
    else
    {
        // Load image from path
        if (loadPng(&(imageLayer.image), imagePath) == false)
        {
            fprintf(stderr, "unable to load %s\n", imagePath);
            exit(EXIT_FAILURE);
        }
    }
    */
    
    
    // TODO: Change height and width to dimensions of screen!
    g_canvas_height = 1440;
    g_canvas_width  = 2560;
    int pitch = g_canvas_width * DISP_CANVAS_BYTES_PER_PIXEL;
    g_canvas_size = pitch * g_canvas_height;
    g_canvas = calloc(1, g_canvas_size);
    assert(g_canvas);
    
    set_start_timestamp("1:00:00", 7);
    
    // Render all text bitmaps
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0

    int text_width;
    int text_height;
    char *text_bitmap_data; 

    get_textdata(startTimestampTextId, &text_width, &text_height, &text_bitmap_data);
    
    initImageWithData(
        &(imageLayer.image),
        VC_IMAGE_RGBA32,
        text_width,
        text_height,
        false,
        text_bitmap_data);
    
    printf("Image dimensions: %dx%d\n", imageLayer.image.width, imageLayer.image.height);
    printf("Image aligned dimensions: %dx%d\n", imageLayer.image.pitch / (imageLayer.image.bitsPerPixel / 8), imageLayer.image.alignedHeight);   
    
    FILE * pFile;
    pFile = fopen ("text.raw", "wb");
    fwrite ((char *) imageLayer.image.buffer, sizeof(char), imageLayer.image.size, pFile);
    fclose (pFile);
    
    //return;

    //---------------------------------------------------------------------

    bcm_host_init();

    //---------------------------------------------------------------------

    DISPMANX_DISPLAY_HANDLE_T display
        = vc_dispmanx_display_open(displayNumber);
    assert(display != 0);

    //---------------------------------------------------------------------

    DISPMANX_MODEINFO_T info;
    int result = vc_dispmanx_display_get_info(display, &info);
    assert(result == 0);

    //---------------------------------------------------------------------

    createResourceImageLayer(&imageLayer, layer);

    //---------------------------------------------------------------------

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    xOffset = TIMESTAMP_PADDING;
    yOffset = info.height - imageLayer.image.height;

    addElementImageLayerOffset(&imageLayer,
                               xOffset,
                               yOffset,
                               display,
                               update);

    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);
    
    IMAGE_LAYER_T endImageLayer;
    
    set_end_timestamp("2:00:00", 7);
    
    // Render all text bitmaps
    text_draw_all(g_canvas, g_canvas_width, g_canvas_height, 0); // is_video = 0

    int end_text_width;
    int end_text_height;
    char *end_text_bitmap_data; 

    get_textdata(endTimestampTextId, &end_text_width, &end_text_height, &end_text_bitmap_data);
    
    initImageWithData(
        &(endImageLayer.image),
        VC_IMAGE_RGBA32,
        end_text_width,
        end_text_height,
        false,
        end_text_bitmap_data);
    
    printf("Image dimensions: %dx%d\n", endImageLayer.image.width, endImageLayer.image.height);
    printf("Image aligned dimensions: %dx%d\n", endImageLayer.image.pitch / (endImageLayer.image.bitsPerPixel / 8), endImageLayer.image.alignedHeight);   

    //---------------------------------------------------------------------

    createResourceImageLayer(&endImageLayer, layer);

    //---------------------------------------------------------------------

    update = vc_dispmanx_update_start(0);
    assert(update != 0);

    xOffset = info.width - endImageLayer.image.width - TIMESTAMP_PADDING;
    yOffset = info.height - endImageLayer.image.height;

    addElementImageLayerOffset(&endImageLayer,
                               xOffset,
                               yOffset,
                               display,
                               update);

    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

    //---------------------------------------------------------------------

    // Sleep for 10 milliseconds every run-loop
    const int sleepMilliseconds = 10;

    while (true)
    {
        usleep(sleepMilliseconds * 1000);
    }

    destroyImageLayer(&imageLayer);

    //---------------------------------------------------------------------

    result = vc_dispmanx_display_close(display);
    assert(result == 0);

    //---------------------------------------------------------------------

    return 0;
}

