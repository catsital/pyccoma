import math
import pyduktape
import PIL.Image

class UnscrambleImg:
    def __init__(self, img, slice_size, seed, output, bmp=None):
        self.img = PIL.Image.open(img)
        self.slice_size = slice_size
        self.seed = seed
        self.bmp = bmp
        self.output = output

    def unscramble(self):
        img_width, img_height = self.img.size
        total_parts = math.ceil(img_width/self.slice_size) * math.ceil(img_height/self.slice_size)
        inds = []
        for i in range(0, total_parts):
            inds.append(i)

        if not self.bmp:
            ctx = PIL.Image.new(mode="RGB",
                                size=(img_width,
                                      img_height),
                                color=(255,255,255))
        else:
            ctx = self.bmp.ctx

        vertical_slices = math.ceil(img_width/self.slice_size)
        horizontal_slices = img_height/self.slice_size
        slices = {}

        def get_slices():
            slices = {}
            for i in range(0, total_parts):
                slice = {}
                row = int(i/vertical_slices)
                col = i-row*vertical_slices
                slice['x'] = col*self.slice_size
                slice['y'] = row*self.slice_size
                slice['width'] = (self.slice_size-(0 if slice['x']+self.slice_size<=img_width else (slice['x']+self.slice_size)-img_width))
                slice['height'] = (self.slice_size-(0 if slice['y']+self.slice_size<=img_height else (slice['y']+self.slice_size)-img_height))
                if str(slice['width'])+"-"+str(slice['height']) not in slices.keys():
                    slices[str(slice['width'])+"-"+str(slice['height'])] = []
                slices[str(slice['width'])+"-"+str(slice['height'])].append(slice)

            return slices

        def get_cols_in_group(slices):
            if len(slices) == 1:
                return 1
            t = 'init'
            for i in range(0, len(slices)):
                if t == 'init':
                    t = slices[i]['y']
                if not t == slices[i]['y']:
                    return i
                    break
            return i

        def get_group(slices):
            self = {}
            self['slices'] = len(slices)
            self['cols'] = get_cols_in_group(slices)
            self['rows'] = len(slices)/self['cols']
            self['width'] = slices[0]['width']*self['cols']
            self['height'] = slices[0]['height']*self['rows']
            self['x'] = slices[0]['x']
            self['y'] = slices[0]['y']
            return self

        slices = get_slices()

        for g in slices:
            group = get_group(slices[g])
            shuffle_ind = [] # shuffle_ind = [0, 308]
            for i in range(0, len(slices[g])):
                shuffle_ind.append(i)
            shuffle_ind = ShuffleSeed().shuffle(shuffle_ind, self.seed)

            for i in range(0, len(slices[g])):
                s = shuffle_ind[i]
                row = int(s/group['cols'])
                col = s-row*group['cols']
                x = col*slices[g][i]['width']
                y = row*slices[g][i]['height']

                tiles = self.img.crop(box=(group['x']+x,
                                           group['y']+y,
                                           group['x']+x+slices[g][i]['width'],
                                           group['y']+y+slices[g][i]['height']))

                ctx.paste(tiles, box=(slices[g][i]['x'],
                                      slices[g][i]['y'],
                                      slices[g][i]['x']+slices[g][i]['width'],
                                      slices[g][i]['y']+slices[g][i]['height']))


        if not self.bmp:
            ctx.save(self.output + ".png")
        else:
            return self.bmp

class ShuffleSeed:
        def __init__(self):
            self.seedrandom_js = open(r'./bower_components/seedrandom/seedrandom.js', 'rt').read()
            self.shuffleseed_js  = open(r'./bower_components/shuffle-seed/shuffle-seed.js', 'rt').read()

        def execute(self, script):
            ctx = pyduktape.DuktapeContext()
            output = ctx.eval_js(script)
            return output

        def shuffle(self, arr, seed):
            # seedrandom.js
            seedrandom = str(self.seedrandom_js) + "n = new Math.seedrandom('{0}'); n();".format(seed)
            # seedshuffle.js
            js = seedrandom + str(self.shuffleseed_js) + "shuffleSeed.shuffle(" + str(arr) + ", '" + seed + "');"
            return self.execute(js)
