# By: Oscar Andersson 2019
import logging
logger = logging.getLogger('gen-alg')
import config.config as cfg

def get_codec_args(decision_vector):
    '''
    Sets input and output arguments for encoding according to the
    decision vector "x" and the encoder.
    '''

    # Set the constant arguments 
    input_args = {
        "pattern_type": 'glob',
        "framerate": "30"
    }
    output_args = {
        "c:v": cfg.video_encoder,
        "format": 'mp4'
    }

    for key in cfg.opt_constants.keys():
        output_args[key] = cfg.opt_constants[key]

    # Add each coding parameter to the output arguments that FFMPEG will use
    for i in range(0, len(cfg.opt_params)):
        arg_val = None
        param_name = cfg.opt_params[i]
        if cfg.opt_type[i] == "c":
            # Categorical coding parameter value
            vector_val = int(round(decision_vector[i]))
            arg_val = cfg.opt_cat_values[param_name][vector_val]
        elif cfg.opt_type[i] == "i":
            # Integer coding parameter value
            arg_val = int(round(decision_vector[i]))
        else:
            # Float coding parameter value
            arg_val = decision_vector[i]
        logger.debug("Adding encoding argument:  Param_name: " + param_name + " arg_val: " + str(arg_val))
        output_args[param_name] = arg_val


    # Add Mega Si prefix for bitrate parameters
    if 'b:v' in output_args: output_args['b:v'] = str(output_args['b:v'])+"M"



    # Set the conditional arguments
    if(cfg.video_encoder == "h264_nvenc" or
       cfg.video_encoder == "hevc_nvenc"): return get_nvenc_args(input_args, output_args, decision_vector)
    elif(cfg.video_encoder == "h264_vaapi" or
         cfg.video_encoder == "hevc_vaapi" or
         cfg.video_encoder == "vp9_vaapi"): return get_vaapi_args(input_args, output_args, decision_vector)
    elif(cfg.video_encoder == "libx264"): return get_libx264_args(input_args, output_args, decision_vector)
    elif(cfg.video_encoder == "libx265"): return get_libx265_args(input_args, output_args, decision_vector)
    elif(cfg.video_encoder == "libsvt_av1"): return get_svtav1_args(input_args, output_args, decision_vector)
    else: raise Exception("Could not find codec")



def get_libx264_args(input_args, output_args, x):
    '''Gets the input and output arguments for the libx264 FFMPEG-encoder'''

    is_two_pass = False

    # Constant bitrate with constrained encoding
    if 'b:v' in output_args: 
        # Checks if one or two passes are to be done
        if output_args["pass"]=="2":
            is_two_pass = True
        else:
            output_args["maxrate"] = output_args['b:v']

            try:
                output_args["bufsize"] = str(round(float(x[0])*float(output_args["bufratio"]), 7)) + "M"
            except Exception:
                logger.critical("Could not set buffer size, quitting...")
                exit(1)

        del output_args["pass"]
        del output_args["bufratio"]


    if cfg.rate_control != "Near-LL":
        # Adjust parameters according to compatability
        if(output_args["coder"] == "vlc"): output_args["trellis"] = 0
        if(output_args["subq"] == 10 and (output_args["aq-mode"]==0 or output_args["trellis"]!= 2)): output_args["subq"] = 9
        if(output_args["psy"] == 1 and not (output_args["subq"] >= 6 and output_args["trellis"] >= 1)): output_args["psy"] == 0


    # Remove tune flag if no tuning parameter is passed
    try:
        if(output_args["tune"] == "none"): del output_args["tune"]
    except Exception:
        logger.debug("No tune parameter found, continuing...")

    try:
        if "deblock-alpha" in output_args:
            output_args["deblock"] = str(output_args["deblock-alpha"]) + ":" + str(output_args["deblock-beta"])
            del output_args["deblock-alpha"]
            del output_args["deblock-beta"]
    except Exception:
        logger.debug("No deblock parameter found, continuing...")

    return input_args, output_args, is_two_pass



def get_libx265_args(input_args, output_args, x):
    '''Gets the input and output arguments for the libx265 FFMPEG-encoder'''
    # Remove tune flag if no tuning parameter is passed
    try:
        if(output_args["tune"] == "none"): del output_args["tune"]
    except Exception:
        logger.debug("No tune parameter found, continuing...")

    x265_params =  "aq-strength=" + str(output_args["aq-strength"])
    del output_args["aq-strength"]
    x265_params += ":ctu=" + str(output_args["ctu"])
    del output_args["ctu"]
    x265_params += ":min-cu-size="  + str(output_args["min-cu-size"])
    del output_args["min-cu-size"]
    x265_params += ":me="  + str(output_args["me"])
    del output_args["me"]
    x265_params += ":aq-mode=" + str(output_args["aq-mode"])
    del output_args["aq-mode"]
    x265_params += ":weightp=" + str(output_args["weightp"])
    del output_args["weightp"]
    x265_params += ":b-pyramid=" + str(output_args["b-pyramid"])
    del output_args["b-pyramid"]
    x265_params += ":weightb=" + str(output_args["weightb"])
    del output_args["weightb"]
    x265_params += ":scenecut=" + str(output_args["scenecut"])
    del output_args["scenecut"]
    x265_params += ":merange=" + str(output_args["merange"])
    del output_args["merange"]
    x265_params += ":subme=" + str(output_args["subme"])
    del output_args["subme"]
    x265_params += ":rc-lookahead=" + str(output_args["rc-lookahead"])
    del output_args["rc-lookahead"]
    x265_params += ":bframe-bias =" + str(output_args["bframe-bias"])
    del output_args["bframe-bias"]

    output_args["x265-params"] = x265_params

    # Checks if one or two passes are to be done
    is_two_pass = True if output_args["pass"]=="2" else False
    del output_args["pass"]

    return input_args, output_args, is_two_pass


def get_nvenc_args(input_args, output_args, x):
    '''Gets the input and output arguments for the nvenc FFMPEG-encoders'''
    
    input_args["hwaccel"] = "nvdec" # Add hardware decoding flag
    
    # Handle incompatible parameter combination
    if output_args["b_ref_mode"] == "2": output_args["weighted_pred"] = 0
    
    return input_args, output_args, False



def get_vaapi_args(input_args, output_args, x):
    '''Gets the input and output arguments for the vaapi FFMPEG-encoders'''
    input_args = apply_vaapi_input_args(input_args)
    output_args["filter_hw_device"] = "foo"
    output_args["vf"] = "format=nv12|vaapi,hwupload"
    if 'b:v' in output_args: 
        if output_args["rc_mode"] == "CBR":
            output_args["maxrate"] = output_args ["b:v"]
        try:
            output_args["bufsize"] = str(round(float(x[0])*float(output_args["bufratio"]), 7)) + "M"
        except Exception:
            logger.critical("Could not set buffer size, quitting...")
            exit(1)
        del output_args["bufratio"]
    return input_args, output_args, False


def get_svtav1_args(input_args, output_args, x):
    '''Gets the input and output arguments for the libsvt-av1 FFMPEG-encoder'''
    return input_args, output_args, False


def apply_vaapi_input_args(input_args):
    input_args["hwaccel"] = "vaapi"
    input_args["hwaccel_output_format"] = "vaapi"
    input_args["init_hw_device"] = "vaapi=foo:/dev/dri/renderD128"
    input_args["hwaccel_device"] = "foo"
    return input_args
